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

from utils import exceptions
from utils.twitter_schema import LookupQueryParams


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
            has_refs: bool = 'referenced_tweets' in self.query_params.tweet_fields
            inc_tweets: List[dict] = response.includes['tweets'] if 'tweets' in response.includes.keys() else None
            inc_users: List[dict] = response.includes['users'] if 'users' in response.includes.keys() else None
            # inc_media: List[dict] = response.includes['media'] if 'media' in response.includes.keys() else None
            if tweets:
                
                # Expansions parsing
                if inc_tweets:
                    ref_tweets = [twalc.Tweet(**tw).to_dict() for tw in inc_tweets]
                if inc_users:
                    authors = [twalc.User(**us).to_dict() for us in inc_users]
                # if inc_media:
                #     media = [twalc.Media(**md) for md in inc_media]
                if has_refs:
                    links = Timeline.__parse_tweet_links(tweets)

                # Original Tweets Parsing
                tweets = [twalc.Tweet(**tw).to_dict() for tw in tweets]
                

                # Expansions dataframes
                if inc_tweets:
                    df_refs   = pd.concat([df_refs, pd.DataFrame(ref_tweets)], axis = 0) if df_refs is not None else pd.DataFrame(ref_tweets)
                if inc_users:
                    df_users  = pd.concat([df_users, pd.DataFrame(authors)], axis = 0) if df_users is not None else pd.DataFrame(authors)
                # if inc_media:
                #     df_media  = pd.concat([df_media, pd.DataFrame(media)], axis = 0) if df_media is not None else pd.DataFrame(media)
                if has_refs:
                    df_links  = pd.concat([df_links, pd.DataFrame(links)], axis = 0) if df_links is not None else pd.DataFrame(links)
                
                # Original tweets dataframe
                df_tweets = pd.concat([df_tweets, pd.DataFrame(tweets)], axis = 0) if df_tweets is not None else pd.DataFrame(tweets)

                if output_user:
                    df_tweets[ident_col] = handle
                
                if save_format == 'csv':
                    # Expansions saving
                    # Full referenced tweets data
                    if inc_tweets:
                        df_refs = Timeline.__fix_floats(df_refs)
                        df_refs.to_csv(save_path % 'ref_tweets', index=False, quoting=csv.QUOTE_ALL,
                                        header=True)
                    # Full author user data
                    if inc_users:
                        df_users = Timeline.__fix_floats(df_users)
                        df_users.to_csv(save_path % 'authors', index=False, quoting=csv.QUOTE_ALL,
                                        header=True)
                    # Full media data
                    # if inc_media:
                    #     df_media.to_csv(save_path % 'media', index=False, quoting=csv.QUOTE_ALL,
                    #                     header=True)
                    # parent-child links for referenced_tweets
                    if has_refs:
                        df_links = Timeline.__fix_floats(df_links)
                        df_links.to_csv(save_path % 'ref_links', index=False, quoting = csv.QUOTE_ALL,
                                    header=True)

                    # Original Tweets Saving
                    df_tweets = Timeline.__fix_floats(df_tweets)
                    df_tweets.to_csv(save_path % 'tweets', index=False, quoting=csv.QUOTE_ALL,
                                    header=True)

                elif save_format == 'json':
                    if inc_tweets:
                        df_refs = Timeline.__fix_floats(df_refs)
                        df_refs.to_json(save_path % 'ref_tweets', orient = 'table')
                    if inc_users:
                        df_users = Timeline.__fix_floats(df_users)
                        df_users.to_json(save_path % 'authors', orient = 'table')
                    # if inc_media:
                        # df_media.to_json(save_path % 'media', orient = 'table')
                    if has_refs:
                        df_links = Timeline.__fix_floats(df_links)
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
    def __fix_floats(df: pd.DataFrame) -> pd.DataFrame:
        #Select all float columns and Float64 columns (coerced after concatenating nullable values)
        float_cols = df.select_dtypes(include=[float, "Float64"])

        # Convert float columns to nullable Int64
        for col in float_cols:
            df[col] = df[col].astype('Int64')

        return df

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
