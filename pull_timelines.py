"""
This script handles the polling of reaction count data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
"""
import os
from tweepy.client import Client
import pprint
from utils.config_schema import TwitterPullConfig
from utils.timeline import Timeline
import pandas as pd


def pull_timelines(config: TwitterPullConfig, client: Client, user_csv: str,
                   output_dir: str = None,
                   handle_column: str = None,
                   author_id_column: str = None,
                   skip_column: str = "skip",
                   output_user: bool = False,
                   use_skip: bool = False,
                   tweets_per_query: int = 100):

    # get search identifiers
    df_handles = pd.read_csv(user_csv)
    if use_skip:
        df_handles = df_handles.loc[df_handles[skip_column] != 1]

    if handle_column and not author_id_column:
        search_ident = list(df_handles[handle_column])
        search_type = 'handle'
    elif author_id_column and not handle_column:
        search_ident = list(df_handles[author_id_column])
        search_type = 'author_id'
    else:
        raise ValueError("`handle_column` and `author_id_column` are mutually exclusive arguments.")

    # set up the timeline
    timeline = Timeline(client, config.twitter.query_params, search_type)

    output_dir = str(config.local.output_dir) if not output_dir else output_dir

    # Pull the tweets
    for ix, ident in enumerate(search_ident):
        print(f"Processing handle {ix + 1}/{len(search_ident)}")
        try:
            timeline.pull(
                ident=ident,
                output_dir=output_dir,
                output_user=output_user,
                ident_col=search_type,
                tweets_per_query=tweets_per_query)
        except Exception as e:
            print(f"Failed to pull timeline for {search_type} {ident}. Error: ", e)
