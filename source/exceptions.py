"""
Custom exceptions used by :mod:`stream`
"""


class MaxRetries(Exception):
    """Raised when the max number of db_engine connection retries has been made on an insert"""
    pass


class ConnectionLimit(Exception):
    """Raised when the filtered stream is at the maximum allowed connection num_tweets."""
    pass


class MissingFieldException(Exception):
    """Raised when the parser is unable to extract required information from the tweet payload"""
    pass

class EmptyTwitterResponseException(Exception):
    """Raised when a twitter API response contains no tweet data."""