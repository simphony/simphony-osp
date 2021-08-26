"""Configuration of OSP-core warnings."""

attributes_cannot_modify_in_place = True
"""Warns when a user fetches a mutable attribute of a CUDS object.

For example `fr = city.City(name='Freiburg', coordinates=[1, 2]);
fr.coordinates`.
"""
