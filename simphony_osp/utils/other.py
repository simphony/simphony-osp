"""Utilities that do not fit in the other categories."""

from typing import Any, Iterator


def take(iterator: Iterator, amount: int) -> Any:
    """Take a specific number of elements from an iterator.

    Given an iterator, creates another iterator that can yield a maximum of
    `amount` items from the original one.

    Args:
        iterator: Original iterator to take items from.
        amount: Maximum number of items to take from the original iterator.
    """
    for i in range(0, amount):
        try:
            yield next(iterator)
        except StopIteration:
            break
