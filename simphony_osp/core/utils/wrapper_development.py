"""Utilities useful for Wrapper developers."""


# General utility methods
def check_arguments(types, *args):
    """Check that the arguments provided are of the certain type(s).

    Args:
        types (Union[Type, Tuple[Type]]): tuple with all the allowed types
        args (Any): instances to check

    Raises:
        TypeError: if the arguments are not of the correct type
    """
    for arg in args:
        if not isinstance(arg, types):
            message = '{!r} is not a correct object of allowed types {}'
            raise TypeError(message.format(arg, types))
