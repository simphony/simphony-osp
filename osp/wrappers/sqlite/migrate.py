"""Migrate sqlite databases with this module."""

import argparse
import logging
import os

from osp.core.session.db.sql_migrate import SqlMigrate
from osp.wrappers.sqlite import SqliteSession

logger = logging.getLogger(__name__)


def install_from_terminal():
    """Migrate sqlite databases from terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Migrate your sqlite database."
    )
    parser.add_argument(
        "db_file", type=str, help="The path to the sqlite database file."
    )

    args = parser.parse_args()

    if not os.path.exists(args.db_file):
        raise FileNotFoundError(args.db_file)

    with SqliteSession(args.db_file) as session:
        m = SqlMigrate(session)
        m.run()


if __name__ == "__main__":
    install_from_terminal()
