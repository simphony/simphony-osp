# from osp.core.session.core_session import CoreSession
# from osp.core.session.file_wrapper_session import FileWrapperSession
# from osp.core.session.session import Session
# from osp.core.session.sim_wrapper_session import SimWrapperSession
# from osp.core.session.wrapper_session import WrapperSession
# from osp.core.session.interfaces.db_wrapper_session import DbWrapperSession
# from osp.core.session.interfaces.sql_wrapper_session import SqlWrapperSession
# from osp.core.session.transport.transport_session_client import
# TransportSessionClient
# from osp.core.session.transport.transport_session_server import
# TransportSessionServer

from osp.core.session.session import Session as _Session

_Session.default_session = _Session()
