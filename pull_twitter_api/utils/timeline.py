import time
from typing import Union, List, Dict
import tweepy.errors
from tweepy.client import Client
from tweepy.tweet import Tweet

import twitteralchemy as twalc

from . import exceptions
from .twitter_schema import LookupQueryParams
from .pull_twitter_response import TimelineResponse


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
             ident_col: str,
             api_response: TimelineResponse = None,
             auto_save: bool = False,
             output_dir: str = None,
             save_format: str = 'csv',
             full_save=True,
             output_user: bool = False,
             tweets_per_query: int = 100):
        """
        Lookup the tweets to get updated reaction counts.

        Args:
            ident: the identifier for the user, an instance of either 'handle' or 'author_id'
            output_dir: location of output data
            ident_col: the name of the output column to save the identifier
            full_save: whether to save extra tweet information (entities, geo, etc.) or not
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

        # Initialize API Response
        if api_response is None:
            api_response = TimelineResponse(auto_save=auto_save,
                                            save_format=save_format,
                                            output_dir=output_dir)

        finished = False
        next_token = None
        num_collected = 0
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
                dict_func = lambda twitter_api_obj: twitter_api_obj.to_full_dict()
                if not full_save:
                    dict_func = lambda twitter_api_obj: twitter_api_obj.to_dict()

                # Expansions parsing
                ref_tweets = [dict_func(tw) for tw in ref_tweets] if ref_tweets else None
                rel_users = [dict_func(us) for us in rel_users] if rel_users else None
                media = [dict_func(md) for md in inc_media] if inc_media else None
                links = Timeline.__parse_tweet_links(tweets) if has_refs else None

                # Original Tweets Parsing
                tweets = [dict_func(twalc.Tweet(**tw)) for tw in tweets]

                # Update response object
                api_response.update_data(ident,
                                         new_links=links,
                                         new_refs=ref_tweets,
                                         new_users=rel_users,
                                         new_tweets=tweets,
                                         new_media=media)

                num_collected += len(tweets)
                print(f"\rCollected {num_collected} tweets for {self.ident_type} {ident}", end='')

            # pagination
            next_token = response.meta.get('next_token', None)
            if next_token is None:
                finished = True
                print('\n' + '-' * 30)
        return api_response

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
