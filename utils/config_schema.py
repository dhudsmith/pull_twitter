import os

from pydantic import BaseModel, SecretStr, FilePath, DirectoryPath

from utils.twitter_schema import LookupQueryParams


# twitter
class TwitterAccount(BaseModel):
    bearer_token: SecretStr
    tweets_per_query: int


class TwitterConfig(BaseModel):
    account: TwitterAccount
    query_params: LookupQueryParams


class LocalConfig(BaseModel):
    handles_csv: FilePath
    output_dir: DirectoryPath
    handle_column: str = "handle"
    skip_column: str = "skip"
    use_skip: bool = True


# Full Config Model for timeline app
class TimelineConfig(BaseModel):
    local: LocalConfig
    twitter: TwitterConfig

    def set_environment_vars(self) -> None:
        # twitter vars
        os.environ['TW_BEARER_TOKEN'] = self.twitter.account.bearer_token.get_secret_value()
        os.environ['TW_TWEETS_PER_QUERY'] = str(self.twitter.account.tweets_per_query)

    class Config:
        extra = "forbid"
        use_enum_values = False
