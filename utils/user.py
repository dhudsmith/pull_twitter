import os.path
import time
from datetime import datetime
from typing import Union, List, Dict
import csv

import pandas as pd
import tweepy.errors
from tweepy.client import Client
from tweepy.tweet import Tweet

import twitteralchemy as twalc

# from utils import exceptions
# from utils.twitter_schema import LookupQueryParams
from . import exceptions
from .twitter_schema import LookupQueryParams


class User:
    """
    The User class manages the connection to the twitter user api
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
        ident: Union[List[str], str], 
        output_dir: str, 
        save_format: str = 'csv', 
        batch_size: int = 100):
        """
        Lookup the users to get updated follower counts.
        Args:
            ident: the identifier for the user, an instance of either 'handle' or 'author_id'
            output_dir: the directory to save the data
            save_format: file type to save results as (currently "csv" and "json" are supported)
            batch_size: number of handles to include in each request.  Maximum for twitter api is 100
        """

        print(f"Pulling user information from given handles")

        # setup save directory
        save_path = f"{output_dir}/data.csv"
        print(f"Saving users to {save_path}")

        ident_batches = [ident[i:i + batch_size] for i in range(0, len(ident), batch_size)]
        num_collected = 0

        for ident_batch in ident_batches:
            try:
                response = self.get_users_data(ident_batch)
            except exceptions.EmptyTwitterResponseException as e:
                print(f"No tweets in the response. Continuing. Exception message: {e}")
                continue
            except exceptions.MaxRetries as e:
                print(f"Max retries exceeded when calling the tweets api. Continuing but may lead to loss of "
                      f"count data. Exception message: {e}")
                continue

            # insert users into file
            users: List[dict] = response.data
            includes: List[dict] = response.includes

            if users:
                users = [twalc.User(**user_dict).to_dict() for user_dict in users]
                if includes:
                    includes = twalc.Includes(**includes)

                df_users = pd.DataFrame(users)
                df_tweets = pd.DataFrame(includes.to_dict()['tweets'])

                if save_format == 'csv':
                    df_users.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL,
                                    header=True)
                    df_tweets.to_csv(save_path % 'pin_tweets.csv', index = False, quoting = csv.QUOTE_ALL,
                                    header = True)
                elif save_format == 'json':
                    df_users.to_json(save_path, orient = 'table')
                    df_tweets.to_json(save_path % 'pin_tweets.csv', orient = 'table')

                num_collected += len(users)
                print(f"\rCollected {num_collected} users", end='')

    def get_users_data(self, ident: Union[List[str], str]):

        params: dict = self.query_params.dict(exclude_unset=True)
        # reformat all params as list type for tweepy
        for key, val in params.items():
            if not isinstance(val, list):
                val = [val]
            params[key] = val

        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                if self.ident_type == 'handle':
                    return self.client.get_users(usernames=ident, **params)
                elif self.ident_type == 'author_id':
                    return self.client.get_users(ids=ident, **params)
                else:
                    raise ValueError(f'type must be one of "handle" or "author_id". Received {self.ident_type}.')
            except tweepy.errors.TwitterServerError as e:
                print("Warning:", e)
                print("Sleeping for 0.1 seconds and retrying")
                retries += 1
                time.sleep(0.1)
