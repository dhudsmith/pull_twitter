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


def pull_users(config_path: str):
    # load the configuration
    with open(config_path, 'r') as f:
        config_yml = yaml.load(f, Loader=yaml.FullLoader)
    config = TwitterPullConfig(**config_yml)
    config.set_environment_vars()
    print(f"Successfully validated configs in {config_path}. Config: \n {pprint.pformat(config.dict())}")

    # tweepy client
    client = Client(bearer_token=os.environ['TW_BEARER_TOKEN'], wait_on_rate_limit=True)

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