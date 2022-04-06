"""For backwords compatibility reason."""

import logging

from osp.wrappers.sqlite.sqlite_session import (  # noqa: F401,E501
    SqliteSession as SqliteWrapperSession,
)

logger = logging.getLogger(__name__)
logger.warning(
    "osp.wrappers.sqlite_wrapper_session.SqliteWrapperSession is "
    "deprecated. Use osp.wrappers.sqlite.SqliteSession instead."
)
