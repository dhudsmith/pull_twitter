import argparse
import yaml
import pprint
import os
from utils.config_schema import TwitterPullConfig
from tweepy.client import Client

# Subcommand imports
from pull_timelines import pull_timelines
from pull_users import pull_users
from pull_query import pull_query

if __name__ == "__main__":

    # CLI and Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config-file", help="YAML configuration file for application", required=True)
    subparsers = parser.add_subparsers()

    # Timeline subcommand
    parser_timeline = subparsers.add_parser("timeline", aliases=["tl"], help = "Pull tweets from users' timelines" )
    parser_timeline.set_defaults(func=pull_timelines)

    # Users subcommand
    parser_users    = subparsers.add_parser("users", aliases=["us"], help = 'Pull user data such as follower counts')
    parser_users.set_defaults(func=pull_users)

    # Query subcommand
    parser_query    = subparsers.add_parser("query", aliases=["qu"], help = 'Pull tweets based on a given query')
    parser_query.set_defaults(func=pull_query)


    # Extract the command line arguments
    args = vars(parser.parse_args())


    # API setup and configuration

    # Load configuration
    with open(args['config_file'], 'r') as f:
        config_yml = yaml.load(f, Loader=yaml.FullLoader)
    config = TwitterPullConfig(**config_yml)
    config.set_environment_vars()
    print(f"Successfully validated configs in {args['config_file']}. Config: \n {pprint.pformat(config.dict())}")

    # tweepy client
    client = Client(bearer_token=os.environ['TW_BEARER_TOKEN'], wait_on_rate_limit=True)

    # Run the application with parsed configuration and initialized client
    args['func'](config, client)