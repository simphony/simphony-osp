"""Interface between the SimPhoNy OSP and SQLite."""

from pathlib import Path

from simphony_osp.interfaces.sqlalchemy.interface import SQLAlchemy


class SQLite(SQLAlchemy):
    """An interface to an SQLite database.

    It just uses the SQLAlchemy wrapper with "sqlite" as prefix, so that the
    user does not need to care about it.
    """

    # TriplestoreInterface
    # ↓ ---------------- ↓

    def open(self, configuration: str, create: bool = False):
        """Open a connection to the database.

        Args:
            configuration: The path pointing to the file containing the
                SQLite database.
            create: Whether to create the database file if it does not exist.
        """
        if not create and not Path(configuration).is_file():
            raise FileNotFoundError(
                f"Database file {configuration} does not " f"exist."
            )
        return super().open(
            configuration="sqlite:///" + configuration, create=create
        )

    # ↑ ---------------- ↑
