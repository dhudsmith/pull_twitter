import os

from pydantic import BaseModel, SecretStr, FilePath, DirectoryPath

from utils.twitter_schema import LookupQueryParams


# twitter
class TwitterAccount(BaseModel):
    bearer_token: SecretStr


class TwitterConfig(BaseModel):
    account: TwitterAccount
    query_params: LookupQueryParams


class LocalConfig(BaseModel):
    output_dir: DirectoryPath


# Full Config Model for app
class TwitterPullConfig(BaseModel):
    local: LocalConfig
    twitter: TwitterConfig

    def set_environment_vars(self) -> None:
        # twitter vars
        os.environ['TW_BEARER_TOKEN'] = self.twitter.account.bearer_token.get_secret_value()

    class Config:
        extra = "forbid"
        use_enum_values = False
