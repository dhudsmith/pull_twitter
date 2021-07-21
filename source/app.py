# TODO: in the case of disconnections, log appropriate metrics needed to retrieve lost data
# TODO: use background thread for reading lines
"""
This script handles the polling of reaction count data using the tweets api. API reference:
https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
"""
import os
from tweepy.client import Client
import yaml
import pprint
from config_schema import TimelineConfig
from timeline import Timeline
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
    handles = list(pd.read_csv(config.local.input_csv)[config.local.handle_column])

    # # set up the timeline
    timeline = Timeline(client, handles, config.twitter.query_params)

    # Run the polling routine
    timeline.pull(output_dir=str(config.local.output_dir))


if __name__ == "__main__":

    # read argument from the command line
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config-file", help="YAML configuration file for application", required=True)
    args = vars(parser.parse_args())

    # run the application
    main(args['config_file'])
