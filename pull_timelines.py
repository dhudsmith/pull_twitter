"""
This script handles the polling of reaction count data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
"""
import os
from tweepy.client import Client
import yaml
import pprint
from utils.config_schema import TimelineConfig
from utils.timeline import Timeline
import pandas as pd


def main(config_path: str):
    # load the configuration
    with open(config_path, 'r') as f:
        config_yml = yaml.load(f, Loader=yaml.FullLoader)
    config = TimelineConfig(**config_yml)
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
    timeline = Timeline(client, config.twitter.query_params)

    # Pull the tweets
    for ix, handle in enumerate(handles):
        print(f"Processing handle {ix+1}/{len(handles)}")
        try:
            timeline.pull(handle, output_dir=str(config.local.output_dir), 
                output_handle = config.local.output_handle, 
                handle_col=config.local.handle_column)
        except Exception as e:
            print(f"Failed to pull timeline for {handle}. Error: ", e)


if __name__ == "__main__":

    # read argument from the command line
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config-file", help="YAML configuration file for application", required=True)
    args = vars(parser.parse_args())

    # run the application
    main(args['config_file'])
