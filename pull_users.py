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


def pull_users(config: TwitterPullConfig, client: Client, handles_csv: str,
               output_dir: str = None,
               handle_column: str = None,
               author_id_column: str = None,
               skip_column: str = "skip",
               use_skip: bool = False):
    # get handles
    df_handles = pd.read_csv(handles_csv)
    if use_skip:
        df_handles = df_handles.loc[df_handles[skip_column] != 1]

    # get search identifiers
    print(handle_column, author_id_column)
    if handle_column and not author_id_column:
        search_ident = list(df_handles[handle_column])
        search_type = 'handle'
    elif author_id_column and not handle_column:
        search_ident = list(df_handles[author_id_column])
        search_type = 'author_id'
    else:
        raise ValueError("`handle_column` and `author_id_column` are mutually exclusive arguments.")

    # set up the user object
    user = User(client, config.twitter.query_params)

    output_dir = str(config.local.output_dir) if not output_dir else output_dir

    try:
        user.pull(ident=search_ident, type=search_type, output_dir=output_dir)
    except Exception as e:
        print(f"Failed to pull user data. Error: ", e)
