"""Utility functions and variables for the remote store implementation."""

import hashlib

ADD_TRIPLES_COMMAND = 'ADD'
COMMIT_COMMAND = 'COMMIT'
DELETE_FILES_COMMAND = 'FILES_DELETE'
FETCH_FILES_COMMAND = 'FILES_FETCH'
FETCH_TRIPLES_COMMAND = 'TRIPLES'
HASH_FILES_COMMAND = 'FILES_HASH'
LOGIN_COMMAND = 'LOGIN'
REMOVE_TRIPLES_COMMAND = 'REMOVE'
RENAME_FILES_COMMAND = 'FILES_RENAME'
ROLLBACK_COMMAND = 'ROLLBACK'
RUN_COMMAND = 'RUN'
UPDATE_FILES_COMMAND = 'FILES_UPDATE'


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
        while True:
            data = f.read(buf_size)
            if not data:
                break
            result.update(data)
    return result.hexdigest()
