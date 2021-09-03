# Setup
In a terminal, navigate to the desired directory and run the following command to clone the repository
```bash
git clone https://github.com/dhudsmith/twitter_timeline.git
```

Next, navigate into the `twitter_timeline` directory and create the python
virtual environment
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
This file contains all input arguments that the script depends on. The application supports
skipping specified handles by placing the value '1' in the "skip" column of the handles csv
file. See the example csv file: `data/celeb_handle_test.csv`. 

From within the `twitter_timeline` folder, run the command (substituting the contents within <>)
```bash
python pull_twitter.py --config_file <path to config yaml file> <subcommand>
```

Available subcommands are detailed below
## Fetch User Tweets

Using the subcommand `timeline` will write data to the output directory specified in the config file. A separate 
sub-folder is created for each non-skipped handle.

## Fetch User Data

Using the subcommand `users` will write data to the output directory specified in the config file. A subfolder called 
"users" will hold all information associated with each handle.

## Querying Tweets

Using the subcommand `query` will write data to the output directory specific in the config file.  A subfolder called
"queries" will hold all tweets returned by each query.

# Issues or suggested features
Please post any suggestions as a new issue on github or reach out to me directly.  
