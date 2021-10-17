import argparse
import yaml
import pprint
import os
import sys
from shutil import copyfile
from datetime import datetime
from utils.config_schema import TwitterPullConfig
from tweepy.client import Client

# Subcommand imports
from utils.pull_timelines import pull_timelines
from utils.pull_users import pull_users
from utils.pull_search import pull_search

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
    parser_timeline.set_defaults(func=pull_timelines)


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
    parser_users.set_defaults(func=pull_users)


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

    # Create output directories
    dt_fmt = '%Y-%m-%d %H.%M.%S'
    timestamp = datetime.now().strftime(dt_fmt)
    subcommand_dir = f"{str(config.local.output_dir)}/{args['name']}"
    output_time_dir = f"{subcommand_dir}/{args['name']}_{timestamp}"
    if not os.path.isdir(subcommand_dir):
        os.mkdir(subcommand_dir)

    os.makedirs(output_time_dir)

    # Save query metadata
    copyfile(args['config_file'], f"{output_time_dir}/config.yaml")
    with open(f"{output_time_dir}/command.txt", "w") as command_file:
        command_file.write(" ".join(sys.argv) + "\n")

    # Clean command keyword arguments
    ignore_args = ['config_file', 'name', 'func']
    command_kwargs = {key: value for key, value in args.items() if (not key in ignore_args) and (value)}
    command_kwargs['output_dir'] = output_time_dir

    # Run the application with parsed configuration and initialized client
    args['func'](config, client, **command_kwargs)
    print("\n")
