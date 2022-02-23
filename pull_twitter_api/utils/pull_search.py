"""
This script handles the polling of user data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
"""
import os
from tweepy.client import Client
import yaml
import pprint
from .twitter_schema import LookupQueryParams
from .tweet_search import TweetSearch
from .pull_twitter_response import SearchResponse
import pandas as pd
from datetime import datetime

def pull_search(client: Client, 
    query_params: LookupQueryParams,
    query: str,
    api_response: SearchResponse = None,
    output_dir: str = None,
    save_format: str = 'csv',
    max_response: int = 100,
    start_time: str = None, 
    end_time: str = None,
    tweets_per_query: int = 100):

    search_query_params = query_params.copy().reformat('tweet')

    # set up the search
    tweet_search = TweetSearch(client, search_query_params)

    # parse times into datetime objects
    if start_time:
        start_time = datetime.fromisoformat(start_time)
    if end_time:
        end_time = datetime.fromisoformat(end_time)

    try:
        response = tweet_search.pull(
            query, 
            output_dir=output_dir, 
            api_response = api_response,
            start_time = start_time, 
            end_time = end_time,
            max_results = max_response, 
            batch_size  = tweets_per_query)

        return response
    except Exception as e:
        print(f"Failed to pull tweets for query. Error: ", e)
        return None
