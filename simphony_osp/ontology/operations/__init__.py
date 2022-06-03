"""Module defining operations for ontology individuals.

Interactive ontology individuals add additional functionality to individuals of
a specific class. For example, SimPhoNY Files have a method to download or
upload an associated file object.
"""

from simphony_osp.ontology.operations.operations import (
    Operations,
    find_operations,
)

__all__ = ["Operations", "find_operations"]
