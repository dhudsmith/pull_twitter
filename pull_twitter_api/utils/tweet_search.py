import os.path
import time
from datetime import datetime
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
from .pull_twitter_response import PullTwitterResponse, SearchResponse

class TweetSearch:
	"""
	The TweetQuery class manages the connection to the twitter query API.
	"""

	def __init__(self,
				tweepy_client: Client,
				query_params: LookupQueryParams):

		# store members
		self.client: Client = tweepy_client
		self.query_params = query_params

	def pull(self, query:str, api_response: SearchResponse = None,
				auto_save: bool = False, output_dir: str = None, save_format: str = 'csv',
				start_time: Union[datetime, str] = None, end_time: Union[datetime, str] = None,
				max_results: int = 100, batch_size: int = 100): # add start and end times
		"""
		Query tweets based on query string

		Args:
			query- Query string to use in searching tweets
			output_dir: parent directory of all twitter_pull results
			save_format: the file type of the output results (csv or json)
			auto_save: whether to continually save to disk after each batch
			start_time: tweets will be searched beginning at this time
			end_time: tweets will be searched at or before this time
			max_results: total number of tweets to return for query
		"""

		print(f"Pulling tweet results using '{query}' search query.")


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

		# Initialize API Response
		if api_response is None:
			api_response = SearchResponse(auto_save = auto_save, 
				save_format = save_format, 
				output_dir = output_dir)

		for batch in batches:
			
			# Get tweet data from twitter api
			try:
				response = self.search_tweets(query, start_time = start_time, end_time = end_time, max_results = batch, next_token=next_token)
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
				links = TweetSearch.__parse_tweet_links(tweets) if has_refs else None

				# Original Tweets Parsing
				tweets = [twalc.Tweet(**tw).to_dict() for tw in tweets]

				# Update response object
				api_response.append_data(new_links = links,
					new_refs = ref_tweets,
					new_users = rel_users,
					new_tweets = tweets,
					new_media = media)

				# update num collection for progress log
				num_collected += len(tweets)
				print(f"\rCollected {num_collected} tweets for query: {query}", end='')

			# pagination
			next_token = response.meta.get('next_token', None)
			if next_token is None:
				print('\n' + '-'*30)
				break

			# Request end time to avoiding 1 request/sec rate limit
			end_time_req = time.time()
			time.sleep(max(0, 1.0 - (end_time_req-start_time_req)))

		return api_response

	def search_tweets(self, query: str, 
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