"""
This script handles the polling of reaction count data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
"""
import os
from tweepy.client import Client
import yaml
import pprint
from .twitter_schema import LookupQueryParams
from .timeline import Timeline
from .pull_twitter_response import TimelineResponse
import pandas as pd


def pull_timelines(client: Client,
                   query_params: LookupQueryParams,
                   user_csv: str,
                   api_response: TimelineResponse = None,
                   output_dir: str = None,
                   save_format: str = None,
                   full_save: bool = True,
                   auto_save: bool = True,
                   handle_column: str = None,
                   author_id_column: str = None,
                   skip_column: str = "skip",
                   output_user: bool = False,
                   use_skip: bool = False,
                   tweets_per_query: int = 100):
    tl_query_params = query_params.copy().reformat('tweet')

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
    timeline = Timeline(client, tl_query_params, search_type)
    response = TimelineResponse()

    # Pull the tweets
    for ix, ident in enumerate(search_ident):
        print(f"Processing handle {ix + 1}/{len(search_ident)}")
        try:
            response = timeline.pull(
                ident=ident,
                output_dir=output_dir,
                api_response=api_response,
                save_format=save_format,
                full_save=full_save,
                auto_save=auto_save,
                output_user=output_user,
                ident_col=search_type,
                tweets_per_query=tweets_per_query)
        except Exception as e:
            print(f"Failed to pull timeline for {search_type} {ident}. Error: ", e)
    return response
