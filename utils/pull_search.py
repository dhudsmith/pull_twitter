"""
This script handles the polling of user data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
"""
import os
from tweepy.client import Client
import yaml
import pprint
from .config_schema import TwitterPullConfig
from .twitter_schema import LookupQueryParams
from .tweet_search import TweetSearch
import pandas as pd
from datetime import datetime

def pull_search(client: Client, 
    query_params: LookupQueryParams, 
    query: str,
    output_dir: str = None,
    save_format: str = 'csv',
    max_response: int = 100,
    start_time: str = None, 
    end_time: str = None,
    tweets_per_query: int = 100):

    # set up the timeline
    tweet_search = TweetSearch(client, query_params)

    #Parse times into datetime objects
    if start_time:
        start_time = datetime.fromisoformat(start_time)
    if end_time:
        end_time = datetime.fromisoformat(end_time)

    try:
        tweet_search.pull(query, output_dir=output_dir, save_format = save_format,
            start_time = start_time, end_time = end_time,
            max_results = max_response, batch_size  = tweets_per_query)
    except Exception as e:
        print(f"Failed to pull tweets for query. Error: ", e)
