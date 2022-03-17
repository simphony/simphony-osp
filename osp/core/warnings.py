"""Configuration of OSP-core warnings."""
from typing import Union

attributes_cannot_modify_in_place = True
"""Warns when a user fetches a mutable attribute of a CUDS object.

For example `fr = city.City(name='Freiburg', coordinates=[1, 2]);
fr.coordinates`.
"""

unreachable_cuds_objects = True
unreachable_cuds_objects_large_dataset_size = 1000
"""Warns when a commit is performed and unreachable CUDS exist.

Disabling this warning can greatly improve the performance of commits when
working with large datasets.

The second parameter `unreachable_cuds_objects_large_dataset_size` controls
the minimum size of a dataset needs to be in order to be considered large.
"""

rdf_properties_warning: Union[bool, None] = True
"""Warns when an RDF file containing RDF properties is read.

RDF properties are not supported by OSP-core, and therefore they are
ignored. If the property is doubly defined also as an OWL data or object
property, then the warning is not emitted.

When this warning setting is set to None, the option to disable it is not
mentioned within the warning.
"""
