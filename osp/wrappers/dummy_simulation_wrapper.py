"""For backwords compatibility reason."""

import logging

from osp.wrappers.simdummy import (  # noqa: F401,E501
    SimDummySession as DummySimWrapperSession,
)

logger = logging.getLogger(__name__)
logger.warning(
    "osp.wrappers.dummy_simulation_wrapper.DummySimWrapperSession is "
    "deprecated. Use osp.wrappers.simdummy.SimDummySession instead."
)
