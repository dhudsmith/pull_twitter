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


def pull_users(config: TwitterPullConfig, client: Client, user_csv: str,
               output_dir: str = None,
               handle_column: str = None,
               author_id_column: str = None,
               skip_column: str = "skip",
               use_skip: bool = False,
               tweets_per_query: int = 100):

    # get search identifiers
    df_users = pd.read_csv(user_csv)
    if use_skip:
        df_users = df_users.loc[df_users[skip_column] != 1]

    if handle_column and not author_id_column:
        search_ident = list(df_users[handle_column])
        ident_type = 'handle'
    elif author_id_column and not handle_column:
        search_ident = list(df_users[author_id_column])
        ident_type = 'author_id'
    else:
        raise ValueError("`handle_column` and `author_id_column` are mutually exclusive arguments.")

    # set up the user object
    user = User(client, config.twitter.query_params, ident_type)

    output_dir = str(config.local.output_dir) if not output_dir else output_dir

    try:
        user.pull(ident=search_ident, output_dir=output_dir, save_format = config.local.save_format, batch_size = tweets_per_query)
    except Exception as e:
        print(f"Failed to pull user data. Error: ", e)

