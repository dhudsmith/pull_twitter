# Setup

First, clone this repository. In a terminal, navigate to the desired directory and run
```bash
git clone https://github.com/dhudsmith/twitter_timeline.git
```

Next, navigate into the `twitter_timeline` directory and create the 
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

Finally, install the necessary dependencies
```bash
python -m pip install -r requirements.txt
```

You can deactivate the virtual environment at any time by running `deactivate`.

# Usage

Activate the virtual environment if it is not already active `source venv/bin/activate`

First create a copy of `configs/template_config.yaml` and fill in following the comments.
This file contains all input arguments that the script depends on. The application supports
skipping specified handles by placing the value '1' in the "skip" column of the handles csv
file. See the example csv file: `data/celeb_handle_test.csv`. 

From within the `twitter_timeline` folder, run the command (substituting the contents within <>)
```bash
python pull_timelines.py --config_file <path to config yaml file>
```


