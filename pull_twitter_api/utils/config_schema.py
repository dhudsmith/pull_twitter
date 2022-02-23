import os
import yaml

from pydantic import BaseModel, SecretStr, FilePath, DirectoryPath

from .twitter_schema import LookupQueryParams


# twitter
class TwitterAccount(BaseModel):
    bearer_token: SecretStr


class TwitterConfig(BaseModel):
    account: TwitterAccount
    query_params: LookupQueryParams


class LocalConfig(BaseModel):
    output_dir: DirectoryPath
    save_format: str


# Full Config Model for app
class PullTwitterConfig(BaseModel):
    local: LocalConfig
    twitter: TwitterConfig

    @classmethod
    def from_file(cls, path_to_config):

        with open(path_to_config, 'r') as f:
            config_yml = yaml.load(f, Loader=yaml.FullLoader)

        config = cls(**config_yml)
        config.set_environment_vars()

        return config

    def set_environment_vars(self) -> None:
        # twitter vars
        os.environ['TW_BEARER_TOKEN'] = self.twitter.account.bearer_token.get_secret_value()

    class Config:
        extra = "forbid"
        use_enum_values = False
