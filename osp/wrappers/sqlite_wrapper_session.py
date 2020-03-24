# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import logging
from osp.wrappers.sqlite.sqlite_session import SqliteSession as SqliteWrapperSession  # noqa: F401,E501

logger = logging.getLogger(__name__)
logger.warning("osp.wrappers.sqlite_wrapper_session.SqliteWrapperSession is "
               "deprecated. Use osp.wrappers.sqlite.SqliteSession instead.")
