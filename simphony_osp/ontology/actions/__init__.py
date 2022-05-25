"""Module defining actions for ontology individuals.

Interactive ontology individuals add additional functionality to individuals of
a specific class. For example, SimPhoNY Files have a method to download or
upload an associated file object.
"""
import sys

from simphony_osp.ontology.actions.actions import Actions, action
from simphony_osp.ontology.actions.catalog import register

if sys.version_info < (3, 8):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


# Retrieve all wrappers from package entry points.
package_entry_points = entry_points()
if sys.version_info >= (3, 10):
    actions = package_entry_points.select(
        group="simphony_osp.ontology.actions"
    )
else:
    actions = package_entry_points.get(
        "simphony_osp.ontology.actions", tuple()
    )
del package_entry_points
actions = {entry_point.name: entry_point.load() for entry_point in actions}
for name, actions in actions.items():
    register(actions, actions.iri)
del actions

__all__ = ["Actions", "action"]
