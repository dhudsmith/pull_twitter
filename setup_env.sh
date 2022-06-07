# run from pull_twitter directory
# note: in slurm-environments (like Clemson palmetto cluster), may need to remove (module del <name>) anaconda before running
conda create -n pull_twitter python=3.8
conda activate pull_twitter
pip install -r requirements.txt --no-cache-dir
