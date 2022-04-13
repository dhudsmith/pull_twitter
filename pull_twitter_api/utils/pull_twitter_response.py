import abc
import json
import yaml
import csv
import os
import pandas as pd
from datetime import datetime

"""
TODO:
	- output_handle in all tweet dfs
	- simplify or check output_dir throughout code and updates
	- __fix_floats method migrate

"""


class PullTwitterResponse(object):

	IDENT = 'base'

	def __init__(self,
		auto_save = False,
		create_dirs = True,
		save_format = 'csv',
		output_dir = None,
		retrieved_dt = None,
		config = None,
		command_dict = None):

		self.auto_save = auto_save
		self.create_dirs = create_dirs
		self.save_format = save_format
		self.output_dir = output_dir
		self.retrieved_dt = datetime.now() if retrieved_dt is None else retrieved_dt
		self.config = config
		self.command_dict = command_dict

		self.has_saved = False

		if auto_save:
			PullTwitterResponse.save(self, command_dict)

	@abc.abstractmethod
	def update_data(self, **kwargs):
		"""
		Update data held in response
		"""
		pass


	def save(self, output_dir = None, **kwargs):
		"""
		Basic saves for all children response objects
		"""

		if self.output_dir is None:
			self.output_dir = output_dir

		if not self.has_saved and self.create_dirs:
			# create output directories if needed
			self.create_output_dir()
			self.save_meta()
			self.has_saved = True

			print("Saving results to ", self.output_dir)


	def save_meta(self, **kwargs):

		# save config used in request
		with open(f"{self.output_dir}/config.yaml", 'w') as f:
			# go through json to convert secret string
			config_secret = json.loads(self.config.json())
			yaml.dump(config_secret, f)

		# save command and parameters used
		command = f"Command - {self.IDENT}\n" + '\n'.join([f"{key} : {value}" for key, value in kwargs.items() if key is not "output_dir"])
		with open(f"{self.output_dir}/params.txt", "w") as pf:
			pf.write(command)


	def create_output_dir(self, output_dir = None) -> None:
		"""
		If they do not exist, create all necessary subdirectories to store data and metadata

		Parameters:
			-subcomm: str
				-Subcommand (timeline, users, search) called
		"""

		if output_dir is None and self.output_dir is None:
			raise ValueError("output_dir must be passed during Response creation or to the save method.")
		self.output_dir = self.output_dir if not output_dir else output_dir

		# Create output directories
		dt_fmt = '%Y-%m-%d %H.%M.%S'
		timestamp = datetime.now().strftime(dt_fmt)
		subcommand_dir = f"{self.output_dir}/{self.IDENT}"
		output_time_dir = f"{subcommand_dir}/{timestamp}"
		if not os.path.isdir(subcommand_dir):
			os.mkdir(subcommand_dir)

		os.makedirs(output_time_dir)

		self.output_dir = output_time_dir



	# Static utility methods

	@staticmethod
	def _update_df(df: pd.DataFrame, new_data: list, append: bool = False) -> pd.DataFrame:
		if new_data:
			new_data_df = pd.DataFrame(new_data)
			
			if append:
				return new_data_df
			else:
				new_df = pd.concat([df, new_data_df], axis = 0) if df is not None else new_data_df
				new_df = new_df.drop_duplicates()

				return new_df
		return None

	@staticmethod
	def _save_df(df: pd.DataFrame, output_dir, fn_suffix, save_format, append: bool = False) -> None:
		save_path = f"{output_dir}/data_{fn_suffix}.{save_format}"

		if df is not None:
			if save_format == 'csv':
				mode = 'a' if append else 'w'
				with open(save_path, mode, encoding = 'utf-8') as f:
					df.to_csv(f, index=False, quoting=csv.QUOTE_ALL,
                                        header=not f.tell(), mode = mode)
			elif save_format == 'json':
				df.to_json(save_path, orient = 'table', mode = 'a' if append else 'w')

	@staticmethod
	def _create_result_subdir(subdir_name, output_dir = None):
		full_path = f"{output_dir}/{subdir_name}"

		if not os.path.isdir(full_path):
			os.mkdir(full_path)

class SingleTimelineResponse(PullTwitterResponse):


	def __init__(self, *args, **kwargs):
		super(SingleTimelineResponse, self).__init__(create_dirs = False, **kwargs)

		self.user = None
		self.df_links = None
		self.df_refs = None
		self.df_users = None
		self.df_tweets = None
		self.df_media = None

		self.has_saved = False

	def update_data(self, 
		new_links = None,
		new_refs = None,
		new_users = None,
		new_tweets = None,
		new_media = None):

		self.df_links  = PullTwitterResponse._update_df(self.df_links, new_links, append = self.auto_save)
		self.df_refs   = PullTwitterResponse._update_df(self.df_refs, new_refs, append = self.auto_save)
		self.df_users  = PullTwitterResponse._update_df(self.df_users, new_users, append = self.auto_save)
		self.df_tweets = PullTwitterResponse._update_df(self.df_tweets, new_tweets, append = self.auto_save)
		self.df_media  = PullTwitterResponse._update_df(self.df_media, new_media, append = self.auto_save)

	def save(self, user_out_dir = None, save_format = 'csv'):

		PullTwitterResponse._save_df(self.df_links, user_out_dir, 'links', save_format, append = self.auto_save)
		PullTwitterResponse._save_df(self.df_refs, user_out_dir, 'refs', save_format, append = self.auto_save)
		PullTwitterResponse._save_df(self.df_users, user_out_dir, 'users', save_format, append = self.auto_save)
		PullTwitterResponse._save_df(self.df_tweets, user_out_dir, 'tweets', save_format, append = self.auto_save)
		PullTwitterResponse._save_df(self.df_media, user_out_dir, 'media', save_format, append = self.auto_save)

		self.has_saved = True

class TimelineResponse(PullTwitterResponse):
	"""
	API Response from calling a timeline-based subcommand
	"""
	IDENT = 'timeline'

	def __init__(self, *args, **kwargs):
		super(TimelineResponse, self).__init__(**kwargs)

		self.timelines = {}


	def update_data(self, 
		user = None,
		new_links = None,
		new_refs = None,
		new_users = None,
		new_tweets = None,
		new_media = None):

		if user not in self.timelines.keys():
			self.timelines[user] = SingleTimelineResponse(auto_save = self.auto_save)

		self.timelines[user].update_data(
			new_links = new_links,
			new_refs = new_refs,
			new_users = new_users,
			new_tweets = new_tweets,
			new_media = new_media,
		)

		if self.auto_save:
			self.save()

	def save(self, output_dir = None):
		super(TimelineResponse, self).save(output_dir = output_dir)

		for user, response in self.timelines.items():
			if not response.has_saved:
				PullTwitterResponse._create_result_subdir(user, output_dir = self.output_dir)
			user_out_dir = f"{self.output_dir}/{user}"
			response.save(user_out_dir = user_out_dir, save_format = self.save_format)


class SearchResponse(PullTwitterResponse):
	"""
	API Response from calling a search-based subcommand
	"""


	IDENT = 'search'

	def __init__(self, *args, **kwargs):
		super(SearchResponse, self).__init__(**kwargs)

		self.df_links = None
		self.df_refs = None
		self.df_users = None
		self.df_tweets = None
		self.df_media = None


	def update_data(self, 
		new_links = None,
		new_refs = None,
		new_users = None,
		new_tweets = None,
		new_media = None):

		self.df_links  = super(SearchResponse, self)._update_df(self.df_links, new_links, append = self.auto_save)
		self.df_refs   = super(SearchResponse, self)._update_df(self.df_refs, new_refs, append = self.auto_save)
		self.df_users  = super(SearchResponse, self)._update_df(self.df_users, new_users, append = self.auto_save)
		self.df_tweets = super(SearchResponse, self)._update_df(self.df_tweets, new_tweets, append = self.auto_save)
		self.df_media  = super(SearchResponse, self)._update_df(self.df_media, new_media, append = self.auto_save)

		if self.auto_save:
			self.save()

	def save(self, output_dir = None):
		super(SearchResponse, self).save(output_dir = output_dir)

		super(SearchResponse, self)._save_df(self.df_links, self.output_dir, 'links', self.save_format, append = self.auto_save)
		super(SearchResponse, self)._save_df(self.df_refs, self.output_dir, 'refs', self.save_format, append = self.auto_save)
		super(SearchResponse, self)._save_df(self.df_users, self.output_dir, 'users', self.save_format, append = self.auto_save)
		super(SearchResponse, self)._save_df(self.df_tweets, self.output_dir, 'tweets', self.save_format, append = self.auto_save)
		super(SearchResponse, self)._save_df(self.df_media, self.output_dir, 'media', self.save_format, append = self.auto_save)


class LookupResponse(PullTwitterResponse):
	"""
	API Response from calling a search-based subcommand
	"""


	IDENT = 'lookup'

	def __init__(self, *args, **kwargs):
		super(LookupResponse, self).__init__(**kwargs)

		self.df_links = None
		self.df_refs = None
		self.df_users = None
		self.df_tweets = None
		self.df_media = None


	def update_data(self, 
		new_links = None,
		new_refs = None,
		new_users = None,
		new_tweets = None,
		new_media = None):

		self.df_links  = super(LookupResponse, self)._update_df(self.df_links, new_links, append = self.auto_save)
		self.df_refs   = super(LookupResponse, self)._update_df(self.df_refs, new_refs, append = self.auto_save)
		self.df_users  = super(LookupResponse, self)._update_df(self.df_users, new_users, append = self.auto_save)
		self.df_tweets = super(LookupResponse, self)._update_df(self.df_tweets, new_tweets, append = self.auto_save)
		self.df_media  = super(LookupResponse, self)._update_df(self.df_media, new_media, append = self.auto_save)

		if self.auto_save:
			self.save()

	def save(self, output_dir = None):
		super(LookupResponse, self).save(output_dir = output_dir)

		super(LookupResponse, self)._save_df(self.df_links, self.output_dir, 'links', self.save_format, append = self.auto_save)
		super(LookupResponse, self)._save_df(self.df_refs, self.output_dir, 'refs', self.save_format, append = self.auto_save)
		super(LookupResponse, self)._save_df(self.df_users, self.output_dir, 'users', self.save_format, append = self.auto_save)
		super(LookupResponse, self)._save_df(self.df_tweets, self.output_dir, 'tweets', self.save_format, append = self.auto_save)
		super(LookupResponse, self)._save_df(self.df_media, self.output_dir, 'media', self.save_format, append = self.auto_save)


class UserResponse(PullTwitterResponse):
	"""
	API Response from calling a user-based subcommand
	"""
	IDENT = 'user'

	def __init__(self, *args, **kwargs):
		super(UserResponse, self).__init__(**kwargs)

		self.df_users = None
		self.df_tweets = None


	def update_data(self, 
		new_users = None,
		new_tweets = None):

		self.df_users  = super(UserResponse, self)._update_df(self.df_users, new_users, append = self.auto_save)
		self.df_tweets = super(UserResponse, self)._update_df(self.df_tweets, new_tweets, append = self.auto_save)

		if self.auto_save:
			self.save()


	def save(self, output_dir = None):
		super(UserResponse, self).save(output_dir = output_dir)

		super(UserResponse, self)._save_df(self.df_users, self.output_dir, 'users', self.save_format, append = self.auto_save)
		super(UserResponse, self)._save_df(self.df_tweets, self.output_dir, 'tweets', self.save_format, append = self.auto_save)

