from enum import Enum
from typing import Union, Optional, List

from pydantic import BaseModel


#
# https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets

class Expansions(Enum):
    attachments_poll_ids = "attachments.poll_ids"
    attachments_media_keys = "attachments.media_keys"
    author_id = "author_id"
    entities_mentions_username = "entities.mentions.username"
    geo_place_id = "geo.place_id"
    in_reply_to_user_id = "in_reply_to_user_id"
    referenced_tweets_id = "referenced_tweets.id"
    referenced_tweets_id_author_id = "referenced_tweets.id.author_id"


class MediaFields(Enum):
    duration_ms = "duration_ms"
    height = "height"
    media_key = "media_key"
    preview_image_url = "preview_image_url"
    type = "type"
    url = "url"
    width = "width"
    public_metrics = "public_metrics"
    non_public_metrics = "non_public_metrics"
    organic_metrics = "organic_metrics"
    promoted_metrics = "promoted_metrics"


class PlaceFields(Enum):
    contained_within = "contained_within"
    country = "country"
    country_code = "country_code"
    full_name = "full_name"
    geo = "geo"
    id = "id"
    name = "name"
    place_type = "place_type"


class PollFields(Enum):
    duration_minutes = "duration_minutes"
    end_datetime = "end_datetime"
    id = "id"
    options = "options"
    voting_status = "voting_status"


class TweetFields(Enum):
    attachments = "attachments"
    author_id = "author_id"
    context_annotations = "context_annotations"
    conversation_id = "conversation_id"
    created_at = "created_at"
    entities = "entities"
    geo = "geo"
    id = "id"
    in_reply_to_user_id = "in_reply_to_user_id"
    lang = "lang"
    non_public_metrics = "non_public_metrics"
    public_metrics = "public_metrics"
    organic_metrics = "organic_metrics"
    promoted_metrics = "promoted_metrics"
    possibly_sensitive = "possibly_sensitive"
    referenced_tweets = "referenced_tweets"
    reply_settings = "reply_settings"
    source = "source"
    text = "text"
    withheld = "withheld"


class UserFields(Enum):
    created_at = "created_at"
    description = "description"
    entities = "entities"
    id = "id"
    location = "location"
    name = "name"
    pinned_tweet_id = "pinned_tweet_id"
    profile_image_url = "profile_image_url"
    protected = "protected"
    public_metrics = "public_metrics"
    url = "url"
    username = "username"
    verified = "verified"
    withheld = "withheld"


class LookupQueryParams(BaseModel):
    expansions: Optional[Union[List[Expansions], Expansions]] = None
    media_fields: Optional[Union[List[MediaFields], MediaFields]] = None
    place_fields: Optional[Union[List[PlaceFields], PlaceFields]] = None
    poll_fields: Optional[Union[List[PollFields], PollFields]] = None
    tweet_fields: Optional[Union[List[TweetFields], TweetFields]] = None
    user_fields: Optional[Union[List[UserFields], UserFields]] = None

    class Config:
        extra = "forbid"
        use_enum_values = True