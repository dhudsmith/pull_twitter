# Setup
Clone the repository and navigate into the repository directory. 

Create the python virtual environment
```bash
# Note: can alternatively use python3.6 or python3.7
virtualenv venv -p python3.8
```

After this completes, activate the environment
```bash
source venv/bin/activate
```
Your terminal line should now start with `(venv)`. 
You can deactivate the virtual environment at any time by running `deactivate`.  

Finally, install the necessary dependencies
```bash
python -m pip install -r requirements.txt
```

# Usage

Activate the virtual environment if it is not already active `source venv/bin/activate`

Fill in the contents of `configs/template_config.yaml` by following the comments.
This file contains all global arguments that each command depends on.

From within the repository folder, run the command (substituting the contents within <>)
```bash
python pull_twitter.py --config_file <path to config yaml file> <subcommand> <subcommand arguments>
```

All data will be saved to the directory indicated by output_dir in the designated config file.  Each subcommand is provided an independent subdirectory to save outputs, and all results are stored in timestamped directories within.

If expansions are designated in the config file, additional output csv's are created to hold the additional data:
* author_id/referenced_tweets.id.author_id/entities.mentions.username
	* for tweet-based outputs, this expansion creates a data file "data_users.csv" holding user data
* referenced_tweets.id
	* for tweet-based outputs, this expansion creates a data file "data_ref_tweets.csv" holding the tweet data for retweets, replies, and quotes
	* an additional data file "data_ref_links.csv" is also created holding the relationships between tweets and reference tweets to link the two outputs

Available subcommands and their arguments are detailed below
## Fetch User Tweets

Using the subcommand `timeline` will collect the tweets in each non-skipped users' timeline, as indicated by the handles_csv parameter.  A separate subdirectory is created for each non-skipped handle.
For help information, run the command:
```python pull_twitter.py timeline --help```

### Arguments
| Full name | Shortened name | Description |
| --------- | -------------- | ----------- |
| --user-csv | -u | CSV containing handles of users to pull timelines for (see data/celeb_handle_test.csv for example) | Yes | N/A |
| --output-user | -ou | Indicates whether to include handles in timeline outputs | No | False |
| --handle-column | -hc | Name of handles column in handles-csv. Incompatible with author-id-column. | No (mutually exclusive with above) | "handle" |
| --author-id-column | -aic | Name of handles column in handles-csv. Incompatible with handle-column. | No (mutually exclusive with above) | "author_id" |
| --skip-column | -sc | Name of column containing skip indicators in handles-csv (skip indicated with a 1) | No | "skip" |
| --use-skip | -usc | Indicates whether to use the skip column to ignore specific handles | No |  |

### Example
```python pull_twitter.py --config-file ./configs/config.yaml timeline -hi "./data/celeb_handle_test.csv" -oh True```

## Fetch User Data

Using the subcommand `users` will collect profile information connected to each non-skipped user as indicated by the handles_csv parameter.
For help information, run the command:
```python pull_twitter.py users --help```

### Arguments
| Full name | Shortened name | Description | Required? | Default |
| --------- | -------------- | ----------- | --------- | ------- |
| --user-csv | -u | CSV containing handles of users to pull timelines for (see data/celeb_handle_test.csv for example) | Yes | N/A |
| --handle-column | -hc | Name of handles column in handles-csv | No (mutually exclusive with above) | "handle" |
| --author-id-column | -aic | Name of handles column in handles-csv. Incompatible with handle-column. | No (mutually exclusive with above) | "author_id" |
| --skip-column | -sc | Name of column containing skip indicators in handles-csv (skip indicated with a 1) | No | "skip" |
| --use-skip | -usc | Indicates whether to use the skip column to ignore specific handles | No | False |

### Example
```python pull_twitter.py --config-file ./configs/config.yaml users -hi "./data/celeb_handle_test.csv"```

## Search Tweets

Using the subcommand `search` will collect tweets that match a provided query string.
For help information, run the command:
```python twitter_pull.py search --help```

### Arguments
| Full name | Shortened name | Description | Required? | Default |
| --------- | -------------- | ----------- | --------- | ------- |
| --query   |       -q       | Query term(s) for searching tweets | Yes | N/A |
| --max-response | -mr | Maximum number of tweets to return using query | No | 100 |
| --start-time | -st | Starting date to search tweets (in format YYYY-MM-DD or isoformat) | No | None |
| --end-time | -et | Ending date to search tweets(in format YYYY-MM-DD or isoformat) | No | None (Current time) |
| --tweets-per-query | -tpq | Number of tweets present in each response from the Twitter API | No | 500 |


### Example
```python pull_twitter.py --config-file ./configs/config.yaml search -q COVID19 -mr 50 -st 2021-08-19 -et 2021-08-21```

# Issues or suggested features
Please post any suggestions as a new issue on github or reach out to me directly.  
