import argparse
import json

import yaml
import pprint
import os
import sys
from shutil import copyfile
from datetime import datetime
from tweepy.client import Client

from pull_twitter_api import PullTwitterAPI

# Subcommand imports
# from pull_twitter_api.utils.pull_timelines import pull_timelines
# from utils.pull_users import pull_users
# from utils.pull_search import pull_search

if __name__ == "__main__":

    # CLI and Argument Parsing
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-cf", "--config-file", help="YAML configuration file for application", required=True)
    subparsers = parser.add_subparsers()

    # Timeline subcommand -----------------------------------------------------------------------
    parser_timeline = subparsers.add_parser("timeline", aliases=["tl"], 
        help = "Pull tweets from users' timelines", 
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_timeline.add_argument("-u", "--user-csv", type=str, 
        help="CSV containing handles of users to pull timelines for", required = True)
    parser_timeline.add_argument("-ou", "--output-user", type=bool, 
        help="Indicates whether to include handles in timeline outputs", required = False,
        default=False)

    timeline_group = parser_timeline.add_mutually_exclusive_group(required=True)
    timeline_group.add_argument("-hc", "--handle-column", type=str, 
        help="Name of handles column in handles-csv", required = False)
    timeline_group.add_argument("-aic", "--author-id-column", type=str, 
        help="Name of handles column in handles-csv")

    parser_timeline.add_argument("-sc", "--skip-column", type=str, 
        help="Name of column containing skip indicators in handles-csv", required = False,
        default="skip")
    parser_timeline.add_argument("-usc", "--use-skip", type=bool, 
        help="Indicates whether to use the skip column to ignore specific handles", required = False,
        default=True)
    parser_timeline.add_argument("-tpq", "--tweets-per-query", type=int, 
        help="Number of tweets present in each response from the Twitter API",
        default=100)
    parser_timeline.set_defaults(name="timeline")


    # Users subcommand -----------------------------------------------------------------------
    parser_users    = subparsers.add_parser("users", aliases=["us"], 
        help = 'Pull user data such as follower counts',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_users.add_argument("-u", "--user-csv", type=str, 
        help="CSV containg handles/author ids of users to pull data for", required = True)

    users_group = parser_users.add_mutually_exclusive_group(required=True)
    users_group.add_argument("-hc", "--handle-column", type=str, 
        help="Name of handles column in handles-csv")
    users_group.add_argument("-aic", "--author-id-column", type=str, 
        help="Name of handles column in handles-csv")

    parser_users.add_argument("-sc", "--skip-column", type=str, 
        help="Name of column containing skip indicators in handles-csv", required = False,
        default = "skip")
    parser_users.add_argument("-usc", "--use-skip", type=bool, 
        help="Indicates whether to use the skip column to ignore specific handles", required = False,
        default = False)
    parser_users.add_argument("-tpq", "--tweets-per-query", type=int,
        help="Number of tweets present in each resposne from the Twitter API", required = False,
        default = 100)
    parser_users.set_defaults(name="users")


    # Query subcommand -----------------------------------------------------------------------
    parser_search    = subparsers.add_parser("search", aliases=["s"], 
        help = 'Pull tweets based on a given query',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_search.add_argument("-q", "--query", type=str, 
        help="Query term(s) for searching tweets", required = True)
    parser_search.add_argument("-mr", "--max-response", type=int, 
        help="Maximum number of tweets to return using query", required = False,
        default = 100)
    parser_search.add_argument("-st", "--start-time", type=str, 
        help="Starting date to search tweets (in format YYYY-MM-DD or isoformat)", required = False,
        default = None)
    parser_search.add_argument("-et", "--end-time", type=str, 
        help="Ending date to search tweets(in format YYYY-MM-DD or isoformat)", required = False,
        default = None)
    parser_search.add_argument("-tpq", "--tweets-per-query", type=int, 
        help="Number of tweets present in each response from the Twitter API", required = False,
        default = 500)
    parser_search.set_defaults(name="search")

    # Lookup subcommand -----------------------------------------------------------------------
    parser_search    = subparsers.add_parser("search", aliases=["s"], 
        help = 'Pull tweets based on a given query',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_search.add_argument("-i", "--id_csv", type=str, 
        help="CSV containing list of tweet ids", required = True)
    parser_search.add_argument("-ic", "--id_col", type=str,
        help="Name of column containing ids in id_csv", required = False)
    parser_search.add_argument("-tpq", "--tweets-per-query", type=int, 
        help="Number of tweets present in each response from the Twitter API", required = False,
        default = 500)
    parser_search.set_defaults(name="search")


    # Extract the command line arguments
    args = vars(parser.parse_args())



    # API Setup and Configuration

    api = PullTwitterAPI(config_path = args['config_file'])
    print(f"Successfully validated configs in {args['config_file']}. Config: \n {pprint.pformat(api.config.dict())}")

    # Clean command keyword arguments
    sc_name = args['name']
    ignore_args = ['config_file', 'name', 'output_dir']
    command_kwargs = {key: value for key, value in args.items() if (not key in ignore_args) and (value)}

    func_dict = {
        'timeline': api.timelines,
        'users': api.users,
        'search': api.search,
        'lookup': api.lookup,
    }

    print(command_kwargs)
    _ = func_dict[sc_name](auto_save = True, **command_kwargs)

    print("\n")
