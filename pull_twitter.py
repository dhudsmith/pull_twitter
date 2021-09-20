import argparse
import yaml
import pprint
import os
from utils.config_schema import TwitterPullConfig
from tweepy.client import Client

# Subcommand imports
from pull_timelines import pull_timelines
from pull_users import pull_users
from pull_search import pull_search

if __name__ == "__main__":

    # CLI and Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config-file", help="YAML configuration file for application", required=True)
    subparsers = parser.add_subparsers()

    # Timeline subcommand
    parser_timeline = subparsers.add_parser("timeline", aliases=["tl"], help = "Pull tweets from users' timelines" )
    parser_timeline.add_argument("-hi", "--handles-csv", type=str, help="CSV containg handles of users to pull timelines for", required = True)
    parser_timeline.add_argument("-oh", "--output-handle", type=bool, help="Indicates whether to include handles in timeline outputs", required = False)
    parser_timeline.add_argument("-hc", "--handle-column", type=str, help="Name of handles column in handles-csv", required = False)
    parser_timeline.add_argument("-sc", "--skip-column", type=str, help="Name of column containing skip indicators in handles-csv", required = False)
    parser_timeline.add_argument("-usc", "--use-skip", type=bool, help="Indicates whether to use the skip column to ignore specific handles", required = False)
    parser_timeline.set_defaults(func=pull_timelines)

    # Users subcommand
    parser_users    = subparsers.add_parser("users", aliases=["us"], help = 'Pull user data such as follower counts')
    parser_users.add_argument("-hi", "--handles-csv", type=str, help="CSV containg handles of users to pull timelines for", required = True)
    parser_users.add_argument("-hc", "--handle-column", type=str, help="Name of handles column in handles-csv", required = False)
    parser_users.add_argument("-sc", "--skip-column", type=str, help="Name of column containing skip indicators in handles-csv", required = False)
    parser_users.add_argument("-usc", "--use-skip", type=bool, help="Indicates whether to use the skip column to ignore specific handles", required = False)
    parser_users.set_defaults(func=pull_users)

    # Query subcommand
    parser_search    = subparsers.add_parser("search", aliases=["s"], help = 'Pull tweets based on a given query')
    parser_search.add_argument("-q", "--query", type=str, help="Query term(s) for searching tweets", required = True)
    parser_search.add_argument("-mr", "--max-response", type=int, help="Maximum number of tweets to return using query", required = False)
    parser_search.add_argument("-st", "--start-time", type=str, help="Starting date to search tweets", required = False)
    parser_search.add_argument("-et", "--end-time", type=str, help="Ending date to search tweets", required = False)
    parser_search.set_defaults(func=pull_search)


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

    print(args)
    ignore_args = ['config_file', 'func']
    command_kwargs = {key:value for key, value in args.items() if (not key in ignore_args) and (value)}

    # Run the application with parsed configuration and initialized client
    args['func'](config, client, **command_kwargs)