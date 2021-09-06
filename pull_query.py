"""
This script handles the polling of user data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
"""
import os
from tweepy.client import Client
import yaml
import pprint
from utils.config_schema import TwitterPullConfig
from utils.tweet_query import TweetQuery
import pandas as pd

def pull_query(config: TwitterPullConfig, client: Client):

    # get query string
    query = config.local.query

    # set up the timeline
    tweet_query = TweetQuery(client, config.twitter.query_params)

    try:
        tweet_query.pull(query, output_dir=str(config.local.output_dir),
            start_time = config.local.start_time, end_time = config.local.end_time,
            max_results = config.local.max_query_response, batch_size  = config.twitter.account.tweets_per_query)
    except Exception as e:
        print(f"Failed to pull tweets for query. Error: ", e)
