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

Available subcommands and their arguments are detailed below
## Fetch User Tweets

Using the subcommand `timeline` will collect the tweets in each non-skipped users' timeline, as indicated by the handles_csv parameter.  A separate subdirectory is created for each non-skipped handle.

### Arguments
| Full name | Shortened name | Description |
| --------- | -------------- | ----------- |
| --user-csv | -u | CSV containing handles of users to pull timelines for (see data/celeb_handle_test.csv for example) |
| --output-user | -ou | Indicates whether to include handles in timeline outputs |
| --handle-column | -hc | Name of handles column in handles-csv. Incompatible with author-id-column. |
| --author-id-column | -aic | Name of handles column in handles-csv. Incompatible with handle-column. |
| --skip-column | -sc | Name of column containing skip indicators in handles-csv (skip indicated with a 1) |
| --use-skip | -usc | Indicates whether to use the skip column to ignore specific handles |
| --tweets-per-query | -tpq | Number of tweets present in each response from the Twitter API |

### Example
```python pull_twitter.py --config-file ./configs/config.yaml timeline -hi "./data/celeb_handle_test.csv" -oh True```

## Fetch User Data

Using the subcommand `users` will collect profile information connected to each non-skipped user as indicated by the handles_csv parameter.

### Arguments
| Full name | Shortened name | Description |
| --------- | -------------- | ----------- |
| --user-csv | -u | CSV containing handles of users to pull timelines for (see data/celeb_handle_test.csv for example) |
| --handle-column | -hc | Name of handles column in handles-csv. Incompatible with author-id-column. |
| --author-id-column | -aic | Name of handles column in handles-csv. Incompatible with handle-column. |
| --skip-column | -sc | Name of column containing skip indicators in handles-csv (skip indicated with a 1) |
| --use-skip | -usc | Indicates whether to use the skip column to ignore specific handles |

### Example
```python pull_twitter.py --config-file ./configs/config.yaml users -hi "./data/celeb_handle_test.csv"```

## Search Tweets

Using the subcommand `search` will collect tweets that match a provided query string.

### Arguments
| Full name | Shortened name | Description |
| --------- | -------------- | ----------- |
| --query   |       -q       | Query term(s) for searching tweets |
| --max-response | -mr | Maximum number of tweets to return using query |
| --start-time | -st | Starting date to search tweets (in format YYYY-MM-DD or isoformat) |
| --end-time | -et | Ending date to search tweets(in format YYYY-MM-DD or isoformat) |
| --tweets-per-query | -tpq | Number of tweets present in each response from the Twitter API |


### Example
```python pull_twitter.py --config-file ./configs/config.yaml search -q COVID19 -mr 50 -st 2021-08-19 -et 2021-08-21```

# Issues or suggested features
Please post any suggestions as a new issue on github or reach out to me directly.  
