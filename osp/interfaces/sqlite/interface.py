"""Interface between the SimPhoNy OSP and SQLite."""

from osp.interfaces.sqlalchemy.interface import SQLAlchemyInterface


class SQLiteInterface(SQLAlchemyInterface):
    """An interface to an SQLite database.

    It just uses the SQLAlchemy wrapper with "sqlite" as prefix, so that the
    user does not need to care about it.
    """

    # TriplestoreInterface
    # ↓ ---------------- ↓

    def open(self, configuration: str):
        """Open a connection to the database.

        Args:
            configuration: The path pointing to the file containing the
                SQLite database.
        """
        return super().open(configuration='sqlite:///' + configuration)

    # ↑ ---------------- ↑
