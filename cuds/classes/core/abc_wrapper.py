# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from uuid import UUID
from abc import ABCMeta, abstractmethod

import cuds.classes
from cuds.utils import check_arguments


class ABCWrapper(object, metaclass=ABCMeta):
    """
    Abstract Base Class for all SimPhoNy wrappers. Defines the methods to be
    implemented and their inputs.
    Matches the API followed in the DataContainer, and checks the input when necessary.
    """

    def __getattr__(self, item):
        """
        Redefines the dot notation access to access the attributes
        that belong to a cuds entity.

        :param item: attribute to get
        :return: value of that attribute if it belongs to an entity or None
        :raises AttributeError: the accessed attribute does not exist
        """
        if item in cuds.classes.cuds_attributes:
            return self._get_cuds_attribute(item)

    @abstractmethod
    def _get_cuds_attribute(self, item):
        """
        Access the attribute of a cuds object through dot notation

        :param item: cuds attribute to get
        :return: value of the attribute
        """
        pass

    def __setattr__(self, name, value):
        """
        Overwrites the dot notation to set the properties,
        also setting the ones belonging to a cuds entity.

        :param name: name of the property
        :param value: value of the property
        """
        if name in cuds.classes.cuds_attributes:
            self._set_cuds_attribute(name, value)
        else:
            self.__dict__[name] = value

    @abstractmethod
    def _set_cuds_attribute(self, name, value):
        """
        Sets the attribute of a cuds object through dot notation

        :param name: name of the cuds attribute
        :param value: value to set
        """
        pass

    @abstractmethod
    def __str__(self):
        """
        Defines the output of str().

        :return: string with the verbose description of the object
        """
        pass

    @abstractmethod
    def add(self, *args):
        """
        Adds (a) cuds object(s) to their respective CUBA key entries using
        a specific function.
        Before adding, check for invalid keys to aviod inconsistencies later.

        :param args: object(s) to add
        :return: reference to itself
        :raises ValueError: adding an element already there
        """
        check_arguments('all_simphony_wrappers', *args)

    @abstractmethod
    def get(self, *keys):
        """
        Returns a wrapped version of the queried elements.

        :param keys: UIDs and/or CUBA types of the elements
        :return: list of objects of that type/uid, or None
        """
        check_arguments((UUID, cuds.classes.CUBA), *keys)

    @abstractmethod
    def remove(self, *args):
        """
        Removes subelements of the current object

        :param args: uid/instance of the subelement to remove
        """
        check_arguments((UUID, cuds.classes.DataContainer), *args)

    @abstractmethod
    def update(self, *args):
        """
        Updates the subelements with newer versions
        :param args: new versions for the subelements
        :raises ValueError: if an element to update does not exist
        """
        check_arguments('all_simphony_wrappers', *args)

    def iter(self, cuba_key=None):
        """
        Iterates over all the objects contained or over a specific type.

        :param cuba_key: type of the objects to iterate through
        """
        if cuba_key is None:
            yield from self._iter_all()
        else:
            check_arguments(cuds.classes.CUBA, cuba_key)
            yield from self._iter_by_key(cuba_key)

    @abstractmethod
    def _iter_all(self):
        """
        Iterates over all the first level children
        """
        pass

    @abstractmethod
    def _iter_by_key(self, cuba_key):
        """
        Iterates over the first level children of a specific type

        :param cuba_key: type of the children to filter
        """
        pass

    @abstractmethod
    def get_cuds(self, *uids):
        """
        Recreate the pure unwrapped CUDS object.

        :param uids: uids of the entities to reconstruct
        :return: list of cuds objects for the provided keys
        """
        check_arguments(UUID, *uids)

    @abstractmethod
    def _wrap(self, *args):
        """
        Returns a wrapped proxy to access the subelements
        :param args: necessary arguments to create the new instance
        :return: new instance for a subelement
        """
        pass
