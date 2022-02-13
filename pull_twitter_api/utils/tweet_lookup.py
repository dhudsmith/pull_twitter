import os.path
from typing import Union, List, Dict
import csv
import time

import pandas as pd
import tweepy.errors
from tweepy.client import Client
from tweepy.tweet import Tweet

import twitteralchemy as twalc

from . import exceptions
from .twitter_schema import LookupQueryParams
from .pull_twitter_response import PullTwitterResponse, LookupResponse

class TweetLookup:
	"""
	The TweetQuery class manages the connection to the twitter query API.
	"""

	def __init__(self,
				tweepy_client: Client,
				query_params: LookupQueryParams):

		# store members
		self.client: Client = tweepy_client
		self.query_params = query_params

	def pull(self, ids: List[str], api_response: LookupResponse = None,
				auto_save: bool = False, output_dir: str = None, save_format: str = 'csv',
				batch_size: int = 100):
		"""
		Query tweets based on query string

		Args:
			id_csv- Csv of tweet ids to fetch
			output_dir: parent directory of all twitter_pull results
			save_format: the file type of the output results (csv or json)
			auto_save: whether to continually save to disk after each batch
		"""

		print(f"Pulling tweet results for {len(ids)} ids.")


		id_batches = [ids[i:i + batch_size] for i in range(0, len(ids), batch_size)]

		num_collected = 0

		# Initialize API Response
		if api_response is None:
			api_response = LookupResponse(auto_save = auto_save, 
				save_format = save_format, 
				output_dir = output_dir)

		for batch in id_batches:
			
			# Get tweet data from twitter api
			try:
				response = self.lookup_tweets(batch)
			except exceptions.EmptyTwitterResponseException as e:
				print(f"No tweets in the response. Continuing. Exception message: {e}")
				continue
			except exceptions.MaxRetries as e:
				print(f"Max retries exceeded when calling the tweets api. Continuing but may lead to loss of "
							f"count data. Exception message: {e}")
				continue

			# Start time of request (avoiding api rate limits)
			start_time_req = time.time()

			# tweets extraction
			tweets: List[dict] = response.data

			# includes and expansions extraction
			includes: List[dict] = twalc.Includes(**(response.includes))
			ref_tweets, rel_users, inc_media = includes.tweets, includes.users, includes.media

			# reference table
			has_refs: bool = 'referenced_tweets' in self.query_params.tweet_fields

			if tweets:

				# Expansions parsing
				ref_tweets = [tw.to_dict() for tw in ref_tweets] if ref_tweets else None
				rel_users = [us.to_dict() for us in rel_users] if rel_users else None
				media = [md.to_dict() for md in inc_media] if inc_media else None
				links = TweetLookup.__parse_tweet_links(tweets) if has_refs else None

				# Original Tweets Parsing
				tweets = [twalc.Tweet(**tw).to_dict() for tw in tweets]

				# Update response object
				api_response.update_data(new_links = links,
					new_refs = ref_tweets,
					new_users = rel_users,
					new_tweets = tweets,
					new_media = media)

				# update num collection for progress log
				num_collected += len(tweets)
				print(f"\rCollected {num_collected} tweets", end='')


			# Request end time to avoiding 1 request/sec rate limit
			end_time_req = time.time()
			time.sleep(max(0, 1.1 - (end_time_req-start_time_req)))

		return api_response

	def lookup_tweets(self, ids: List[str]):
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
				return self.client.get_tweets(ids, **params)
			except tweepy.errors.TwitterServerError as e:
				print("Warning:", e)
				print("Sleeping for 0.1 seconds and retrying")
				retries += 1
				time.sleep(0.1)

	@staticmethod
	def __parse_tweet_links(tweets: List[Tweet]) -> List[dict]:
		tweet_links = []
		for tweet in tweets:
			if tweet['referenced_tweets'] is not None:
				for ref in tweet['referenced_tweets']:
					new_link = {
						'parent_id': tweet['id'], 
						'id': ref['id'],
						'type': ref['type']
					}
					tweet_links.append(new_link)
		return tweet_links