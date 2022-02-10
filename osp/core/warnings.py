"""Configuration of OSP-core warnings."""

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
