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

def pull_query(config_path: str):
    # load the configuration
    with open(config_path, 'r') as f:
        config_yml = yaml.load(f, Loader=yaml.FullLoader)
    config = TwitterPullConfig(**config_yml)
    config.set_environment_vars()
    print(f"Successfully validated configs in {config_path}. Config: \n {pprint.pformat(config.dict())}")

    # tweepy client
    client = Client(bearer_token=os.environ['TW_BEARER_TOKEN'], wait_on_rate_limit=True)

    # get query string
    query = config.local.query

    # set up the timeline
    tweet_query = TweetQuery(client, config.twitter.query_params)

    try:
        tweet_query.pull(query, output_dir=str(config.local.output_dir),
            start_time = config.local.start_time, end_time = config.local.end_time,
            max_results = config.local.max_query_response)
    except Exception as e:
        print(f"Failed to pull user data. Error: ", e)
