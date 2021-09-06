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

class TweetQuery:
	"""
	The TweetQuery class manages the connection to the twitter query API.
	"""

	def __init__(self,
				tweepy_client: Client,
				query_params: LookupQueryParams):

		# store members
		self.client: Client = tweepy_client
		self.query_params = query_params

	def pull(self, query:str, output_dir: str, 
				start_time: Union[datetime, str] = None, end_time: Union[datetime, str] = None,
				max_results: int = 100, batch_size: int = 100): # add start and end times
		"""
		Query tweets based on query string

		Args:
			query- Query string to use in searching tweets
			output_dir: parent directory of all twitter_pull results
			start_time: tweets will be searched beginning at this time
			end_time: tweets will be searched at or before this time
		"""

		print(f"Pulling tweet results using '{query}' search query.")

		# setup save directory
		save_dir = f"{output_dir}/queries"
		timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		if not os.path.isdir(save_dir):
			os.mkdir(save_dir)
		save_path = f"{save_dir}/{timestamp}.csv"
		print(f"Saving tweets to {save_path}")

		num_batches = (max_results//batch_size) + 1
		batches = [batch_size] * num_batches
		last_batch_size = max_results % batch_size
		if last_batch_size < 10:
			batches[-1] = 10
			if num_batches > 1:
				batches[-2] = batch_size - (10 - last_batch_size)
		else:
			batches[-1] = last_batch_size
		


		next_token = None
		num_collected = 0
		for batch in batches:

			# Get tweet data from twitter api
			try:
				response = self.query_tweets(query, start_time = start_time, end_time = end_time, max_results = batch, next_token=next_token)
			except exceptions.EmptyTwitterResponseException as e:
				print(f"No tweets in the response. Continuing. Exception message: {e}")
				continue
			except exceptions.MaxRetries as e:
				print(f"Max retries exceeded when calling the tweets api. Continuing but may lead to loss of "
							f"count data. Exception message: {e}")
				continue

			# insert tweets into file
			tweets: List[dict] = response.data
			if tweets:
				tweets = [twalc.Tweet(**tw).to_dict() for tw in tweets]

				df_tweets = pd.DataFrame(tweets)

				df_tweets.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL, mode='a',
									header=False if os.path.isfile(save_path) else True)
				num_collected += len(tweets)
				print(f"\rCollected {num_collected} tweets for query: {query}", end='')

			# pagination
			next_token = response.meta.get('next_token', None)
			if next_token is None:
				print('\n' + '-'*30)
				break


	def query_tweets(self, query: str, 
					start_time: Union[datetime, str] = None, 
					end_time: Union[datetime, str] = None,
					max_results: int = 10,
					next_token: str = None):

		params: dict = self.query_params.dict(exclude_unset=True)
		# reformat all params as list type for tweepy
		for key, val in params.items():
			if not isinstance(val, list):
				val = [val]
			params[key] = val

		if start_time:
			params['start_time'] = start_time
		if end_time:
			params['end_time'] = end_time

		params['next_token'] = next_token
		params['max_results'] = max_results

		max_retries = 5
		retries = 0
		while retries < max_retries:
			try:
				return self.client.search_all_tweets(query, **params)
			except tweepy.errors.TwitterServerError as e:
				print("Warning:", e)
				print("Sleeping for 0.1 seconds and retrying")
				retries += 1
				time.sleep(0.1)