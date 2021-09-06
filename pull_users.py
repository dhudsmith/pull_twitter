"""
This script handles the polling of user data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by
"""
import os
from tweepy.client import Client
import yaml
import pprint
from utils.config_schema import TwitterPullConfig
from utils.user import User
import pandas as pd


def pull_users(config: TwitterPullConfig, client: Client):

    # get handles
    df_handles = pd.read_csv(config.local.handles_csv)
    if config.local.use_skip:
        df_handles = df_handles.loc[df_handles[config.local.skip_column] != 1]
    handles = list(df_handles[config.local.handle_column])

    # set up the timeline
    user = User(client, config.twitter.query_params)

    try:
        user.pull(handles, output_dir=str(config.local.output_dir))
    except Exception as e:
        print(f"Failed to pull user data. Error: ", e)