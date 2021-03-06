"""
This script handles the polling of tweet data using the tweets lookup api. API reference:
https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
"""
import os
from tweepy.client import Client
import yaml
import pprint
from .twitter_schema import LookupQueryParams
from .tweet_lookup import TweetLookup
from .pull_twitter_response import LookupResponse
import pandas as pd
from datetime import datetime


def pull_lookup(client: Client,
                query_params: LookupQueryParams,
                id_csv: str,
                api_response: LookupResponse = None,
                output_dir: str = None,
                save_format: str = 'csv',
                full_save: bool = True,
                auto_save: bool = False,
                id_col: str = 'id',
                skip_column: str = "skip",
                use_skip: bool = False,
                tweets_per_query: int = 100):
    lookup_query_params = query_params.copy().reformat('tweet')

    df_ids = pd.read_csv(id_csv)
    if use_skip:
        df_ids = df_ids.loc[df_ids[skip_column] != 1]

    ids = list(df_ids[id_col])

    # set up the search
    tweet_lookup = TweetLookup(client, lookup_query_params)

    try:
        response = tweet_lookup.pull(
            ids,
            output_dir=output_dir,
            api_response=api_response,
            save_format=save_format,
            full_save=full_save,
            auto_save=auto_save,
            batch_size=tweets_per_query)

        return response
    except Exception as e:
        print(f"Failed to pull tweets for ids. Error: ", e)
        return None
