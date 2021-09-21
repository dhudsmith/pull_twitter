"""
This script handles the polling of user data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
"""
import os
from tweepy.client import Client
import yaml
import pprint
from utils.config_schema import TwitterPullConfig
from utils.tweet_search import TweetSearch
import pandas as pd
from datetime import datetime

def pull_search(config: TwitterPullConfig, client: Client, query: str,
    output_dir: str = None,
    max_response: int = 100,
    start_time: str = None, 
    end_time: str = None):

    # set up the timeline
    tweet_search = TweetSearch(client, config.twitter.query_params)

    #Parse times into datetime objects
    if start_time:
        start_time = datetime.fromisoformat(start_time)
    if end_time:
        end_time = datetime.fromisoformat(end_time)

    output_dir = str(config.local.output_dir) if not output_dir else output_dir

    try:
        tweet_search.pull(query, output_dir=output_dir,
            start_time = start_time, end_time = end_time,
            max_results = max_response, batch_size  = config.twitter.account.tweets_per_query)
    except Exception as e:
        print(f"Failed to pull tweets for query. Error: ", e)
