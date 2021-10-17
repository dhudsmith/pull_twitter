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

from utils import exceptions
from utils.twitter_schema import LookupQueryParams

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

	def pull(self, query:str, output_dir: str, save_format: str = 'csv',
				start_time: Union[datetime, str] = None, end_time: Union[datetime, str] = None,
				max_results: int = 100, batch_size: int = 100): # add start and end times
		"""
		Query tweets based on query string

		Args:
			query- Query string to use in searching tweets
			output_dir: parent directory of all twitter_pull results
			save_format: the file type of the output results (csv or json)
			start_time: tweets will be searched beginning at this time
			end_time: tweets will be searched at or before this time
			max_results: total number of tweets to return for query
		"""

		print(f"Pulling tweet results using '{query}' search query.")

		# setup save directory
		save_path = f"{output_dir}/data_%s.{save_format}"
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
		df_links, df_refs, df_users, df_tweets, df_media = None, None, None, None, None
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

			start_time_req = time.time()

			# insert tweets into file
			tweets: List[dict] = response.data
			has_refs: bool = 'referenced_tweets' in self.query_params.tweet_fields
			inc_tweets: List[dict] = response.includes['tweets'] if 'tweets' in response.includes.keys() else None
			inc_users: List[dict] = response.includes['users'] if 'users' in response.includes.keys() else None
			# inc_media: List[dict] = response.includes['media'] if 'media' in response.includes.keys() else None

			if tweets:

				# Expansions parsing
				if inc_tweets:
					ref_tweets = [twalc.Tweet(**tw) for tw in inc_tweets]
				if inc_users:
					authors = [twalc.User(**us) for us in inc_users]
				# if inc_media:
				#     media = [twalc.Media(**md) for md in inc_media]
				if has_refs:
					links = TweetSearch.__parse_tweet_links(tweets)

				# Original Tweets Parsing
				tweets = [twalc.Tweet(**tw).to_dict() for tw in tweets]

				# Expansions dataframes
				if inc_tweets:
					df_refs   = pd.concat([df_refs, pd.DataFrame(ref_tweets)], axis = 1) if df_refs is not None else pd.DataFrame(ref_tweets)
				if inc_users:
					df_users  = pd.concat([df_users, pd.DataFrame(authors)], axis = 1) if df_users is not None else pd.DataFrame(authors)
				# if inc_media:
				#     df_media  = pd.concat([df_media, pd.DataFrame(media)], axis = 1) if df_media is not None else pd.DataFrame(media)
				if has_refs:
					df_links  = pd.concat([df_links, pd.DataFrame(links)], axis = 1) if df_links is not None else pd.DataFrame(links)

				# Original tweets dataframe
				df_tweets = pd.concat([df_tweets, pd.DataFrame(tweets)], axis = 1) if df_tweets is not None else pd.DataFrame(tweets)

				if save_format == 'csv':
					# Expansions saving
					# Full referenced tweets data
					if inc_tweets:
						df_refs.to_csv(save_path % 'ref_tweets', index=False, quoting=csv.QUOTE_ALL,
										header=True)
					# Full author user data
					if inc_users:
						df_users.to_csv(save_path % 'authors', index=False, quoting=csv.QUOTE_ALL,
										header=True)
					# Full media data
					# if inc_media:
					#     df_media.to_csv(save_path % 'media', index=False, quoting=csv.QUOTE_ALL,
					#                     header=True)
					# parent-child links for referenced_tweets
					if has_refs:
						df_links.to_csv(save_path % 'ref_links', index=False, quoting = csv.QUOTE_ALL,
										header=True)

					# Original Tweets Saving
					df_tweets.to_csv(save_path % 'tweets', index=False, quoting=csv.QUOTE_ALL,
									header=True)

				elif save_format == 'json':
					if inc_tweets:
						df_refs.to_json(save_path % 'ref_tweets', orient = 'table')
					if inc_users:
						df_users.to_json(save_path % 'authors', orient = 'table')
					# if inc_media:
					    # df_media.to_json(save_path % 'media', orient = 'table')
					if has_refs:
						df_links.to_json(save_path % 'ref_links', orient = 'table')
					df_tweets.to_json(save_path, orient = 'table')

				num_collected += len(tweets)
				print(f"\rCollected {num_collected} tweets for query: {query}", end='')

			# pagination
			next_token = response.meta.get('next_token', None)
			if next_token is None:
				print('\n' + '-'*30)
				break

			# Avoiding 1 request/sec rate limit
			end_time_req = time.time()
			time.sleep(max(0, 1.0 - (end_time_req-start_time_req)))




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