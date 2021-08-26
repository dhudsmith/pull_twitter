import os.path
import time
from datetime import datetime
from typing import Union, List, Dict
import csv

import pandas as pd
import tweepy.errors
from tweepy.client import Client
from tweepy.tweet import Tweet

import twitteralchemy as twalc

from utils import exceptions
from utils.twitter_schema import LookupQueryParams

class User:
	"""
		The User class manages the connection to the twitter user api
	"""

	def __init__(self,
				tweepy_client: Client,
				query_params: LookupQueryParams):

        # store members
		self.client: Client = tweepy_client
		self.query_params = query_params

	def pull(self, handles:str, output_dir: str, batch_size: int = 100):
		"""
		Lookup the users to get updated follower counts.

		Args:
	    	batch_size: number of handles to include in each request.  Maximum for twitter api is 100
		"""

		print(f"Pulling user information from given handles")

		# setup save directory
		save_dir = f"{output_dir}/users"
		timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
		if not os.path.isdir(save_dir):
			os.mkdir(save_dir)
		save_path = f"{save_dir}/{timestamp}.csv"
		print(f"Saving users to {save_path}")


		handle_batches = [handles[i:i+batch_size] for i in range(0, len(handles), batch_size)]
		num_collected = 0

		for handle_batch in handle_batches:
			try:
				response = self.get_users_data(handle_batch)
			except exceptions.EmptyTwitterResponseException as e:
				print(f"No tweets in the response. Continuing. Exception message: {e}")
				continue
			except exceptions.MaxRetries as e:
				print(f"Max retries exceeded when calling the tweets api. Continuing but may lead to loss of "
							f"count data. Exception message: {e}")
				continue

			# insert users into file
			users: List[dict] = response.data
			if users:
				users = [twalc.User(**user_dict).to_dict() for user_dict in users]

				df_users = pd.DataFrame(users)

				df_users.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL, mode='a',
								header=False if os.path.isfile(save_path) else True)
				num_collected += len(users)
				print(f"\rCollected {num_collected} users", end='')


	def get_users_data(self, handles: Union[List[str], str]):

		params: dict = self.query_params.dict(exclude_unset=True)
		# reformat all params as list type for tweepy
		for key, val in params.items():
			if not isinstance(val, list):
				val = [val]
			params[key] = val
        
		max_retries = 5
		retries = 0
		while retries < max_retries:
			try:
				return self.client.get_users(usernames = handles, **params)
			except tweepy.errors.TwitterServerError as e:
				print("Warning:", e)
				print("Sleeping for 0.1 seconds and retrying")
				retries += 1
				time.sleep(0.1)
