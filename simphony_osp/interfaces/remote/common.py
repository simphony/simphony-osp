"""Utility functions and variables for the remote store implementation."""

import hashlib
import urllib.parse
from enum import Enum
from typing import Optional, Tuple


class COMMAND(str, Enum):
    """Collection of remote interface commands."""

    # Interface commands
    ROOT = "ROOT"
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    POPULATE = "POPULATE"
    COMMIT = "COMMIT"
    COMPUTE = "COMPUTE"

    # Base graph commands
    STORE_OPEN = "STORE_OPEN"
    STORE_CLOSE = "STORE_CLOSE"
    STORE_ADD = "STORE_ADD"
    STORE_TRIPLES = "STORE_TRIPLES"
    STORE_REMOVE = "STORE_REMOVE"
    STORE_COMMIT = "STORE_COMMIT"
    STORE_ROLLBACK = "STORE_ROLLBACK"

    # Triplestore commands
    ADD = "ADD"
    TRIPLES = "TRIPLES"
    REMOVE = "REMOVE"

    # File commands
    SAVE = "SAVE"
    LOAD = "LOAD"
    DELETE = "DELETE"
    HASH = "HASH"
    RENAME = "RENAME"

    # Remote interface commands
    HASATTR = "HASATTR"
    AUTHENTICATE = "AUTHENTICATE"


def get_hash(file_path: str) -> str:
    """Get the hash of the given file.

    Args:
        file_path (path): A path to a file

    Returns:
        HASH: A sha256 HASH object
    """
    buf_size = 4096
    result = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = True
        while data:
            data = f.read(buf_size)
            result.update(data)
    return result.hexdigest()


def parse_uri(uri: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse the given uri and return uri, username, password.

    Args:
        uri: The URI to parse
    """
    if uri is None:
        return None, None, None
    parsed = urllib.parse.urlparse(uri)
    username = parsed.username
    password = parsed.password
    parsed = list(parsed)
    if username or password:
        parsed[1] = parsed[1].split("@")[1]
    uri = urllib.parse.urlunparse(parsed)
    return uri, username, password
