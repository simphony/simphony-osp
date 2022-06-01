"""Module defining operations for ontology individuals.

Interactive ontology individuals add additional functionality to individuals of
a specific class. For example, SimPhoNY Files have a method to download or
upload an associated file object.
"""
import os
import sys
from pathlib import Path

from simphony_osp.ontology.operations.catalog import register
from simphony_osp.ontology.operations.operations import (
    Operations,
    find_operations_in_operations_folder,
    find_operations,
)

if sys.version_info < (3, 8):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

__all__ = ["Operations", "find_operations"]


# Retrieve operations from package entry points.
package_entry_points = entry_points()
if sys.version_info >= (3, 10):
    operations = package_entry_points.select(
        group="simphony_osp.ontology.operations"
    )
else:
    operations = package_entry_points.get(
        "simphony_osp.ontology.operations", tuple()
    )
del package_entry_points
operations = {
    entry_point.name: entry_point.load() for entry_point in operations
}
for name, operations in operations.items():
    register(operations, operations.iri)
del operations

# Retrieve operations from the operation folder in the user's home directory.
path = (
    os.environ.get("SIMPHONY_OPERATIONS_DIR")
    or Path.home() / ".simphony-osp" / "operations"
)
operations = find_operations_in_operations_folder(path)
for operations in operations:
    register(operations, operations.iri)
del operations
