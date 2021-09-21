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


def pull_timelines(config: TwitterPullConfig, client: Client, handles_csv: str, 
    output_dir: str = None,
    handle_column: str = "handle", 
    skip_column: str = "skip",
    output_handle: bool = False, 
    use_skip: bool = False):

    # get handles
    df_handles = pd.read_csv(handles_csv)
    if use_skip:
        df_handles = df_handles.loc[df_handles[skip_column] != 1]
    handles = list(df_handles[handle_column])

    # set up the timeline
    timeline = Timeline(client, config.twitter.query_params)

    output_dir = str(config.local.output_dir) if not output_dir else output_dir

    # Pull the tweets
    for ix, handle in enumerate(handles):
        print(f"Processing handle {ix+1}/{len(handles)}")
        try:
            timeline.pull(handle, output_dir=output_dir, 
                output_handle = output_handle, 
                handle_col = handle_column)
        except Exception as e:
            print(f"Failed to pull timeline for {handle}. Error: ", e)
