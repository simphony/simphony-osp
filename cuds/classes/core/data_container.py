import uuid
from cuds.utils import check_arguments
from ..generated.cuba import CUBA


class DataContainer(dict):
    """
    A DataContainer instance

    The DataContainer object is implemented as a python dictionary whose keys
    are restricted to the instance's `restricted_keys`, default to the CUBA
    enum members.
    """

    def __init__(self, name):
        """
        Initialization follows the behaviour of the python dict class.
        """
        super(DataContainer, self).__init__()

        # These are the allowed CUBA keys (faster to convert to set for lookup)
        self.restricted_keys = frozenset(CUBA)

        self.name = name
        self.uid = uuid.uuid4()

    def __setitem__(self, key, value):
        """
        Set/Update the key value only when the key is a CUBA key.

        :param key: key in the dictionary
        :param value: new value to assign to the key
        :raises ValueError: unsupported key provided (not a CUBA key)
        """
        if key in self.restricted_keys:
            super(DataContainer, self).__setitem__(key, value)
        else:
            message = "Key {!r} is not in the supported keywords"
            raise ValueError(message.format(key))

    def add(self, *args):
        """
        Adds (a) cuds object(s) to their respective CUBA key entries.

        :param args: object(s) to add
        :raises ValueError: adding an element already there
        """
        # Check now for invalid keys to avoid inconsistencies later
        check_arguments(DataContainer, *args)
        for arg in args:
            key = arg.cuba_key
            # There are already entries for that CUBA key
            if key in self.keys():
                if arg.uid not in self.__getitem__(key).keys():
                    self.__getitem__(key)[arg.uid] = arg
                else:
                    message = '{!r} is already in the container'
                    raise ValueError(message.format(arg))
            else:
                self.__setitem__(key, {arg.uid: arg})

    def get(self, *keys):
        """
        Returns the contained elements of a certain type/uid.

        :param keys: UIDs and/or CUBA types of the elements
        :return: list of objects of that type, or None
        """
        check_arguments((uuid.UUID, CUBA), *keys)
        output = []
        for key in keys:
            # get by UID
            if isinstance(key, uuid.UUID):
                for element in self.values():
                    if key in element:
                        output.append(element[key])
                        break
                # if not found
                else:
                    output.append(None)
            # get by CUBA key
            else:
                try:
                    output.extend(self.__getitem__(key).values())
                except KeyError:
                    # Add None if that key is not contained
                    output.append(None)
        return output

    def remove(self, *args):
        """
        Removes an element from the DataContainer.

        :param args: object or UID of the object to remove
        """
        check_arguments((uuid.UUID, DataContainer), *args)
        for arg in args:
            # Erase a UID
            cuba_key = None
            if isinstance(arg, uuid.UUID):
                for cuba_key in self.keys():
                    # UID is a key on that dict
                    if arg in self.__getitem__(cuba_key):
                        del self.__getitem__(cuba_key)[arg]
                        break
            else:
                cuba_key = arg.cuba_key
                del self.__getitem__(cuba_key)[arg.uid]

            # Erase the CUBA key entry if empty
            if not self.__getitem__(cuba_key):
                self.__delitem__(cuba_key)

    def update(self, *args):
        """
        Updates the object with the newer objects.

        :param args: element(s) to update
        :raises ValueError: if an element to update does not exist
        """
        check_arguments(DataContainer, *args)
        for arg in args:
            key = arg.cuba_key
            # Update the entry for the entity's key
            try:
                self.__getitem__(key)[arg.uid] = arg
            except KeyError:
                message = "{} does not exist. Add it first"
                raise ValueError(message.format(arg))

    def iter(self, cuba_key=None):
        """
        Iterates over all the objects contained or over a specific type.

        :param cuba_key: type of the objects to iterate through
        """
        if cuba_key is None:
            # Dictionary with entities of the same CUBA key
            for element in self.values():
                for item in element.values():
                    yield item
        else:
            check_arguments(CUBA, cuba_key)
            try:
                for item in self.__getitem__(cuba_key).values():
                    yield item
            # No elements for that key
            except KeyError:
                pass
