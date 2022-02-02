import os.path
import time
from datetime import datetime
from typing import Union, List, Dict
import csv

import pandas as pd
import numpy as np
import tweepy.errors
from tweepy.client import Client
from tweepy.tweet import Tweet

import twitteralchemy as twalc

from . import exceptions
from .twitter_schema import LookupQueryParams

class Timeline:
    """
    The Timeline class manages the connection to the twitter timeline API.
    """

    def __init__(self,
                 tweepy_client: Client,
                 query_params: LookupQueryParams,
                 ident_type: str):

        # store members
        self.client: Client = tweepy_client
        self.query_params = query_params
        self.ident_type = ident_type

    def pull(self,
             ident: str,
             output_dir: str,
             ident_col: str,
             save_format: str = 'csv',
             output_user: bool = False,
             tweets_per_query: int = 100):
        """
        Lookup the tweets to get updated reaction counts.

        Args:
            ident: the identifier for the user, an instance of either 'handle' or 'author_id'
            output_dir: location of output data
            ident_col: the name of the output column to save the identifier
            output_user: weather or not to output the user identifier with each tweet
            tweets_per_query: num_tweets the number of database entries processed. Mainly for debugging purposes.
        """

        print(f"Pulling timeline for {self.ident_type} {ident}.")

        # attempt to get user_id
        if self.ident_type == 'handle':
            try:
                user_id = self.client.get_user(username=ident).data.id
            except Exception as e:
                print(f"Failed to get user id for {ident}")
                raise e

            print(f"Successfully retrieved user_id {user_id} for @{ident}.")
        elif self.ident_type == 'author_id':
            user_id = ident
        else:
            raise ValueError(f'type must be one of "handle" or "author_id". Received {self.ident_type}')

        # setup save directory
        save_dir = f"{output_dir}/{ident}"
        os.mkdir(save_dir)
        save_path = f"{save_dir}/data_%s.{save_format}"
        print(f"Saving tweets to {save_path}")        


        finished = False
        next_token = None
        num_collected = 0
        df_links, df_refs, df_users, df_tweets, df_media = None, None, None, None, None
        while not finished:
            # Get tweet data from twitter api
            try:
                response = self.get_tweets(user_id, next_token=next_token, tweets_per_query=tweets_per_query)
            except exceptions.EmptyTwitterResponseException as e:
                print(f"No tweets in the response. Continuing. Exception message: {e}")
                continue
            except exceptions.MaxRetries as e:
                print(f"Max retries exceeded when calling the tweets api. Continuing but may lead to loss of "
                      f"count data. Exception message: {e}")
                continue

            # insert tweets into file
            tweets: List[dict] = response.data

            # includes and expansions extraction
            includes: List[dict] = twalc.Includes(**(response.includes))
            ref_tweets, rel_users, inc_media = includes.tweets, includes.users, includes.media

            # reference table
            has_refs: bool = 'referenced_tweets' in self.query_params.tweet_fields
            
            if tweets:
                
                if has_refs:
                    links = Timeline.__parse_tweet_links(tweets)

                # Original Tweets Parsing
                tweets = [twalc.Tweet(**tw).to_dict() for tw in tweets]
                

                # Expansions dataframes
                if ref_tweets:
                    new_inc_tweets = pd.DataFrame([tweet.to_dict() for tweet in ref_tweets])
                    df_refs   = pd.concat([df_refs, new_inc_tweets], axis = 0) if df_refs is not None else new_inc_tweets
                    df_refs = df_refs.drop_duplicates()
                if rel_users:
                    new_rel_users = pd.DataFrame([user.to_dict() for user in rel_users])
                    df_users  = pd.concat([df_users, new_rel_users], axis = 0) if df_users is not None else new_rel_users
                    df_users = df_users.drop_duplicates()
                if inc_media:
                    new_media = pd.DataFrame([media.to_dict() for media in inc_media])
                    df_media  = pd.concat([df_media, new_media], axis = 0) if df_media is not None else new_media
                    df_media = df_media.drop_duplicates()
                if has_refs:
                    new_links = pd.DataFrame(links)
                    df_links  = pd.concat([df_links, new_links], axis = 0) if df_links is not None else new_links
                    df_links = df_links.drop_duplicates()

                # Original tweets dataframe
                new_tweets = pd.DataFrame(tweets)
                df_tweets = pd.concat([df_tweets, new_tweets], axis = 0) if df_tweets is not None else new_tweets

                if output_user:
                    df_tweets[ident_col] = ident
                

                if save_format == 'csv':
                    # Expansions saving
                    # Full referenced tweets data
                    if ref_tweets:
                        df_refs.to_csv(save_path % 'ref_tweets', index=False, quoting=csv.QUOTE_ALL,
                                        header=True)
                    # Full author user data
                    if rel_users:
                        df_users.to_csv(save_path % 'users', index=False, quoting=csv.QUOTE_ALL,
                                        header=True)
                    # Full media data
                    if inc_media:
                        df_media.to_csv(save_path % 'media', index=False, quoting=csv.QUOTE_ALL,
                                        header=True)
                    # parent-child links for referenced_tweets
                    if has_refs:
                        df_links.to_csv(save_path % 'ref_links', index=False, quoting = csv.QUOTE_ALL,
                                    header=True)

                    # Original Tweets Saving
                    df_tweets.to_csv(save_path % 'tweets', index=False, quoting=csv.QUOTE_ALL,
                                    header=True)

                elif save_format == 'json':
                    if ref_tweets:
                        df_refs.to_json(save_path % 'ref_tweets', orient = 'table')
                    if rel_users:
                        df_users.to_json(save_path % 'users', orient = 'table')
                    if inc_media:
                        df_media.to_json(save_path % 'media', orient = 'table')
                    if has_refs:
                        df_links.to_json(save_path % 'ref_links', orient = 'table')
                        
                    df_tweets = Timeline.__fix_floats(df_tweets)
                    df_tweets.to_json(save_path, orient = 'table')
                num_collected += len(tweets)
                print(f"\rCollected {num_collected} tweets for {self.ident_type} {ident}", end='')

            # pagination
            next_token = response.meta.get('next_token', None)
            if next_token is None:
                finished = True
                print('\n' + '-' * 30)

    def get_tweets(self, ids: Union[List[Union[int, str]], Union[int, str]],
                   since_id: str = None,
                   next_token: str = None,
                   tweets_per_query: int = 100):

        params: dict = self.query_params.dict(exclude_unset=True)
        # reformat all params as list type for tweepy
        for key, val in params.items():
            if not isinstance(val, list):
                val = [val]
            params[key] = val

        if since_id:
            params['since_id'] = since_id
        params['pagination_token'] = next_token
        params['max_results'] = tweets_per_query

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                return self.client.get_users_tweets(ids, **params)
            except tweepy.errors.TwitterServerError as e:
                print("Warning:", e)
                print("Sleeping for 0.1 seconds and retrying")
                retries += 1
                time.sleep(0.1)

    @staticmethod
    def __parse_tweet_links(tweets: List[Tweet]) -> List[dict]:
        tweet_links = []
        for tweet in tweets:
            if tweet['referenced_tweets'] is not None:
                for ref in tweet['referenced_tweets']:
                    new_link = {
                        'parent_id': tweet['id'], 
                        'id': ref['id'],
                        'type': ref['type']
                    }
                    tweet_links.append(new_link)
        return tweet_links

    @staticmethod
    def _get_reaction_counts(tweet: Tweet) -> Dict:
        """
        Helper method to convert a tweet object into a dict containing the required reaction counts
        Args:
            tweet (): the Tweet object

        Returns: A dictionary containing the number of 'likes', 'retweets', 'replies', and 'quotes'.
        """

        metrics = tweet.public_metrics
        return {'likes': metrics['like_count'],
                'retweets': metrics['retweet_count'],
                'replies': metrics['reply_count'],
                'quotes': metrics['quote_count']}
