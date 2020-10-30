"""Migrate sqlite databases with this module."""

import os
import argparse
import logging
from osp.wrappers.sqlite import SqliteSession
from osp.core.session.db.sql_migrate import SqlMigrate

logger = logging.getLogger(__name__)


class SqliteMigrate(SqlMigrate):
    """Migrate sqlite tables to the latest db schema."""

    def __init__(self, db_file):
        """Initialize the migration tool with an SqliteSession."""
        super().__init__(SqliteSession(db_file))


def install_from_terminal():
    """Migrate sqlite databases from terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Migrate your sqlite database."
    )
    parser.add_argument("db_file", type=str,
                        help="The path to the sqlite database file.")

    args = parser.parse_args()

    if not os.path.exists(args.db_file):
        raise FileNotFoundError(args.db_file)

    m = SqliteMigrate(args.db_file)
    m.run()


if __name__ == "__main__":
    install_from_terminal()
