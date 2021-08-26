import argparse
from pull_timelines import pull_timelines
from pull_users import pull_users

if __name__ == "__main__":

    # read argument from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config-file", help="YAML configuration file for application", required=True)
    subparsers = parser.add_subparsers()

    parser_timeline = subparsers.add_parser("timeline", aliases=["tl"], help = "Pull tweets from users' timelines" )
    parser_timeline.set_defaults(func=pull_timelines)

    parser_users    = subparsers.add_parser("users", aliases=["us"], help = 'Pull user data such as follower counts')
    parser_users.set_defaults(func=pull_users)

    args = vars(parser.parse_args())

    # run the application
    args['func'](args['config_file'])