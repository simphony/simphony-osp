# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from uuid import UUID
from abc import ABCMeta, abstractmethod

from cuds.utils import check_arguments
from cuds.classes import CUBA, DataContainer


class ABCWrapper(object):
    """


    """
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def __getattr__(self, item):
        pass

    @abstractmethod
    def __setattr__(self, name, value):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def add(self, *args):
        check_arguments('all_simphony_wrappers', *args)

    @abstractmethod
    def get(self, *keys):
        check_arguments((UUID, CUBA), *keys)

    @abstractmethod
    def remove(self, *args):
        check_arguments((UUID, DataContainer), *args)

    @abstractmethod
    def update(self, *args):
        check_arguments('all_simphony_wrappers', *args)

    @abstractmethod
    def iter(self, cuba_key=None):
        pass

    @abstractmethod
    def get_cuds(self, *uids):
        check_arguments(UUID, *uids)

    @abstractmethod
    def _wrap(self, *args):
        pass
