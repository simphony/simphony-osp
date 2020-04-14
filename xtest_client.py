import logging
from osp.core import cuba
from osp.wrappers.dataspace import DataspaceSession

logging.getLogger("osp.core").setLevel(logging.DEBUG)

with DataspaceSession("127.0.0.1", 4587) as session:
    wrapper = cuba.wrapper(session=session)
    file = cuba.file(path="setup.py")
    wrapper.add(file, rel=cuba.active_relationship)
    session.commit()
    input(session._file_destination)
