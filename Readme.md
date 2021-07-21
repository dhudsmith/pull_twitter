# lookup
This application polls a tweet dataset for numbers of likes, retweets, replies and quotes.

# Module contents

* `app.py`: the main program. This loops through all tweets in the reference database table, queries their 
  reaction counts from the twitter api, and writes the result to the specified database table.
  `app.py` has two required arguments: `--config-file` which points to the correct yaml file
  (more on configuration later) and `--run-mode` which takes the values `dev` or `prod`.
  
* `config_schema.py`: this file defines the model/schema for input configuration. This defines the 
  `LookupConfig` class which parses and validates the user's specified configuration file 
  at the start of the main application. Clear feedback is given for invalid configurations.
  
* `config_template.yaml`: this is a template configuration file with some comments explaining
the various fields. This must be completed with user-specific data and provided as an argument to `app.py`.
  WARNING: your config file will contain sensitive information! Under no circumstances should your config file be
  committed to the git repository!
  
* `deploy_lookup_codeengine.sh`: this bash script packages the lookup application and deploys it
to IBM Code Engine. More on deployment below.
  
* `Dockerfile`: this Dockerfile is used to create the deployment image for Code Engine. This
image starts from the base image specified in the top-level `docker/` directory for this repository.

* `Poll.py`: this script contains most of the logic for updating the reaction counts
by querying the twitter api.
  
* `Readme.md`: the current file!

# Configuration
The behavior of the application is controlled by providing a yaml configuration file. 
See `config_template.yaml` for a template. This section briefly describes how to fill 
these values for a new deployment of the lookup application. Coming soon...

# Deployment 
This app is deployed as a "job" on IBM Cloud Code Engine (CE). The following steps walk through
the deployment process. This process is packaged into the `deploy_lookup_codeengine.sh` bash script.

### Container setup
In a terminal, navigate to the root directory of the twitter-stream project. Execute
```shell
docker build . --file src/modules/lookup/Dockerfile -t us.icr.io/smrf/lookup:<tag>
```
Run the container locally to make sure it works
```shell
docker run -it --rm us.icr.io/smrf/lookup:<tag> 
```
Assuming that worked, push this to the ibm cloud container registry using
```shell
docker push us.icr.io/smrf/lookup:<tag>
```

### Configuring the environmental variables
All environmental variables are set by `app.py` based on the provided configuration file.

### Creating the job
Before using the container, CE must be granted access to the container registry.
This can be done through the CE gui. At some point, you are required to provide an API key. 
An appropriate key can be created by going to Manage > Access (IAM) > API Keys and creating
a new key. You should only need to do this once or possibly not at all if someone has already
configured this for the CE instance and namespace you are using. You can get the name of your registry by running
`ibmcloud ce registry list`.

You can create the job by executing a command like
```shell
ibmcloud ce job create \
    --name <job_name> \
    --image us.icr.io/stream/lookup:<tag> \
    -rs ibm-container-registry \
    --cpu 0.25 -m 1G
```
Note: this command will fail if the job already exists. 
To update, simply replace the `create` command with `update`. 

There are many more options that can be set when creating a job. To see them, 
execute `ibmcloud ce job create --help`. The above uses default settings for 
the runtime. 


### Submitting a job
Now that the job has been created, we can submit the job. This will cause the job
to run. Execute:
```shell
ibmcloud ce jr submit --job <jobname>
```
You can check running jobs with `ibmcloud ce jr list`.

### Scheduling a job
Code engine allows to setup a cron-based schedule for a job. For example, the following creates a schedule to run every
at the top of every 2nd hour
```shell
ibmcloud ce sub ping create \
    --name <sub_name> \
    --destination-type job \
    --destination <job_name> \
    --schedule '0 */2 * * *'
```

# Logging

