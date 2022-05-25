"""Classes supporting the definition and use of custom actions in SimPhoNy.

This file contains an `Actions` abstract class that wrapper or package
developers can use to implement specific functionality for certain ontology
classes (e.g. download and upload commands for files, multiplying EMMO
vectors, ...).

The `action` decorator is used to declare only specific methods of the
subclass of `Actions` implemented by the wrapper or package developer as
actions. The rest of the methods will not be shown to the user.

Instances of the `ActionsNamespace` class are accessed as the `actions`
property of ontology individuals. The `ActionsNamespace` instances let the
user access the actions defined for each ontology individual. Each individual
has an associated instance of the subclass of `Actions` that the
wrapper or package developer has defined.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from functools import wraps
from typing import TYPE_CHECKING, Callable, Dict, Iterator, Set, Tuple, Type

from simphony_osp.ontology.actions import catalog

if TYPE_CHECKING:
    from simphony_osp.ontology import OntologyIndividual


__all__ = ["Actions", "ActionsNamespace", "action"]


class Actions(ABC):
    """Define actions for an ontology class."""

    @property
    @abstractmethod
    def iri(self) -> str:
        """IRI of the ontology class for which actions should be registered."""
        pass

    @abstractmethod
    def __init__(self, individual: "OntologyIndividual"):
        """Initialization of your instance of the actions.

        It is recommended to save the individual that is received as an
        argument to an instance attribute, as the actions to be executed are
        supposed to be related to it.
        """
        pass


def action(func: Callable):
    """Decorator registering an action."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return func(self, *args, **kwargs)

    wrapper._is_simphony_action = True
    return wrapper


class ActionsNamespace(Mapping):
    """Access the actions associated to an ontology individual.

    Instances of the `ActionsNamespace` class are accessed as the `actions`
    property of ontology individuals. The `ActionsNamespace` instances let the
    user access the actions defined for each ontology individual. Each
    individual has an associated instance of the subclass of `Actions` that the
    wrapper or package developer has defined.
    """

    _individual: "OntologyIndividual"
    _instances: Dict[Type, Actions]

    def __init__(self, individual: "OntologyIndividual"):
        """Initialize the `ActionsNamespace`."""
        self._instances = dict()
        self._individual = individual

    def __getattr__(self, item: str):
        """Get an action by name using dot notation."""
        try:
            result = self[item]
        except KeyError as e:
            raise AttributeError(str(e)) from e
        return result

    def __getitem__(self, key: str) -> Callable:
        """Get an action by name using brackets."""
        results = {
            (class_, method)
            for name, class_, method in self._all_methods
            if name == key
        }
        if len(results) > 1:
            raise RuntimeError(
                f"More than one action available under the name {key} for "
                f"individual {self._individual} of classes "
                f"{','.join(str(x) for x in self._individual.classes)} "
                f"available ."
            )
        elif len(results) == 0:
            raise KeyError(
                f"No action with name {key} available for {self._individual} "
                f"of classes "
                f"{','.join(str(x) for x in self._individual.classes)}."
            )
        class_, method = results.pop()
        instance = self._instances.get(class_) or class_(
            individual=self._individual
        )

        @wraps(method)
        def function(*args, **kwargs):
            return method(instance, *args, **kwargs)

        return function

    def __len__(self) -> int:
        """Number of actions available for the individual."""
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator[str]:
        """Iterate over the names of the available actions."""
        yield from {name for name, class_, method in self._all_methods}

    @property
    def _all_methods(self) -> Set[Tuple[str, Type, Callable]]:
        """Get a set will all the available actions for the individual."""
        classes = (
            class_.identifier for class_ in self._individual.superclasses
        )
        results = {
            (name, class_, method)
            for identifier in classes
            for name, (class_, method) in catalog.get(
                identifier, dict()
            ).items()
        }
        return results
