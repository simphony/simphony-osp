"""The data space store connects SimPhoNy to a data space."""
import os
import pathlib
from base64 import b64encode
from pathlib import Path
from typing import BinaryIO, Optional

from rdflib import Graph, URIRef
from rdflib.term import Identifier

from simphony_osp.interfaces.interface import Interface
from simphony_osp.interfaces.remote.common import get_hash


class DataspaceInterface(Interface):
    """The data space interface connects SimPhoNy to a data space."""

    _identifier: Identifier = URIRef("https://www.simphony-osp.eu/SQLAlchemy")

    _database_path: Optional[Path] = None
    _files_path: Optional[Path] = None

    _uri: Optional[str] = None

    # Interface
    # ↓ ----- ↓

    entity_tracking: bool = False

    def open(self, configuration: str, create: bool = False):
        """Open the specified dataspace."""
        path = pathlib.Path(configuration).absolute()
        if not create:
            if not path.is_dir():
                raise FileNotFoundError(f"Folder {path} not found")
            if not (path / "database.db").is_file():
                raise FileNotFoundError(
                    f'Database {path / "database.db"} ' f"not found."
                )
            if not (path / "files").is_dir():
                raise FileNotFoundError(
                    f'Folder {path / "files"} ' f"not found."
                )

        uri = "sqlite:///" + str(path / "database.db")
        if self._uri is not None and self._uri != uri:
            raise RuntimeError(
                f"A different dataspace {self._uri}" f"is already open!"
            )

        os.makedirs(path, exist_ok=True)
        os.makedirs(path / "files", exist_ok=True)
        self.base = Graph("SQLAlchemy", identifier=self._identifier)
        self.base.open(uri, create=create)
        self._uri = uri
        self._database_path = path / "database.db"
        self._files_path = path / "files"

    def close(self):
        """Close the dataspace."""
        if self.base is not None:
            self.base.close(commit_pending_transaction=False)
            self._uri = None
            self.base = None
            self._database_path = None
            self._files_path = None

    def commit(self):
        """Commit pending changes to the triple store."""
        # The `InterfaceDriver` will simply add the triples to the base graph
        # and commit them. Nothing to do here.
        pass

    def populate(self):
        """The base graph does not need to be populated. Nothing to do."""
        pass

    def save(self, key: str, file: BinaryIO) -> None:
        """Save a file."""
        file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")
        buf_size = 1024
        with open(self._files_path / file_name, "wb") as new_file:
            data = True
            while data:
                data = file.read(buf_size)
                new_file.write(data)

    def load(self, key: str) -> BinaryIO:
        """Load a file."""
        file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")
        return open(self._files_path / file_name, "rb")

    def delete(self, key: str) -> None:
        """Delete a file."""
        file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")
        (self._files_path / file_name).unlink()

    def hash(self, key: str) -> str:
        """Hash a file."""
        file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")
        return get_hash(str(self._files_path / file_name))

    def rename(self, key: str, new_key: str) -> None:
        """Rename a file."""
        file_name = b64encode(bytes(key, encoding="UTF-8")).decode("UTF-8")
        new_file_name = b64encode(bytes(new_key, encoding="UTF-8")).decode(
            "UTF-8"
        )
        (self._files_path / file_name).rename(self._files_path / new_file_name)

    # ↑ ----- ↑
