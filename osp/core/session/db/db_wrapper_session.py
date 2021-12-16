"""An abstract session containing method useful for all database backends."""

from abc import abstractmethod
import itertools
import logging

from rdflib import OWL, RDF, URIRef

from osp.core.ontology.datatypes import UID
from osp.core.ontology.namespace_registry import namespace_registry
from osp.core.session.buffers import BufferContext, EngineContext
from osp.core.session.result import returns_query_result
from osp.core.session.wrapper_session import WrapperSession, consumes_buffers
from osp.core.utils.general import CUDS_IRI_PREFIX

logger = logging.getLogger(__name__)


class DbWrapperSession(WrapperSession):
    """Abstract class for a DB Wrapper Session."""

    @consumes_buffers
    def commit(self):
        """Commit the changes in the buffers to the database."""
        self.log_buffer_status(BufferContext.USER)
        self._check_cardinalities()
        self._init_transaction()
        try:
            root_obj = self._registry.get(self.root)
            added, updated, deleted = self._buffers[BufferContext.USER]
            self._apply_added(root_obj, added)
            self._apply_updated(root_obj, updated)
            self._apply_deleted(root_obj, deleted)
            self._reset_buffers(BufferContext.USER)
            self._unreachable_warning(root_obj)
            self._commit()
        except Exception as e:
            self._rollback_transaction()
            raise e
        self.expire_all()

    @returns_query_result
    def load_by_oclass(self, oclass):
        """Load cuds_object with given OntologyClass.

        Will also return cuds objects of subclasses of oclass.

        Args:
            oclass (OntologyClass): Load cuds objects with this ontology class.

        Yields:
            Cuds: The list of loaded cuds objects
        """
        if self.root is None:
            raise RuntimeError("This Session is not yet initialized. "
                               "Add it to a wrapper first.")
        for subclass in oclass.subclasses:
            yield from self._load_by_oclass(subclass)

    def _store(self, cuds_object):
        """Store and object in the database.

        Args:
            cuds_object (Cuds): The Cuds object to add.
        """
        initialize = self.root is None
        super()._store(cuds_object)

        if initialize:
            with EngineContext(self):
                self._init_transaction()
                try:
                    self._initialize()
                    self._load_first_level()
                    self._commit()
                except Exception as e:
                    self._rollback_transaction()
                    raise type(e)(str(e)) from e

    def _commit(self):
        """Commit to the database."""
        self._engine.commit()

    @abstractmethod
    def _initialize(self):
        """Initialize the database. Create missing tables etc."""

    @abstractmethod
    def _apply_added(self, root_obj, buffer):
        """Add the added cuds_objects to the engine."""

    @abstractmethod
    def _apply_updated(self, root_obj, buffer):
        """Update the updated cuds_objects in the engine."""

    @abstractmethod
    def _apply_deleted(self, root_obj, buffer):
        """Delete the deleted cuds_objects from the engine."""

    @abstractmethod
    def _load_first_level(self):
        """Load the first level of children of the root from the database."""

    @abstractmethod
    def _init_transaction(self):
        """Initialize the transaction."""

    @abstractmethod
    def _rollback_transaction(self):
        """Cancel the transaction."""

    @abstractmethod
    def close(self):
        """Close the connection to the database."""

    @abstractmethod
    def _load_by_oclass(self, oclass):
        """Load the cuds_object with the given ontology class.

        Args:
            oclass (OntologyClass): The OntologyClass of the cuds objects.

        Returns:
            Cuds: The loaded cuds_object.
        """

    @staticmethod
    def compute_auth(username, password, handshake):
        """Will be called on the client, after the handshake.

        This method should produce an object that is able to authenticate
        the user.
        The __init__() method of the session should have a keyword "auth",
        that will have the output of this function as a value.
        --> The user can be authenticated on __init__()

        Args:
            username (str): The username as encoded in the URI.
            password (str): The password as encoded in the URI.
            handshake (Any): The result of the hanshake method.

        Returns:
            Any: Any JSON serializable object that is able to authenticate
            the user.
        """
        return username, password

    # OVERRIDE
    def _expire_neighour_diff(self, old_cuds_object, new_cuds_object,
                              uids):
        # do not expire if root is loaded
        x = old_cuds_object or new_cuds_object
        if x and x.uid != self.root:
            super()._expire_neighour_diff(old_cuds_object, new_cuds_object,
                                          uids)

    def _is_cuds_iri(self, iri):
        uid = UID(iri)
        return uid in self._registry.keys() or \
            uid == UID(0) or iri.startswith(CUDS_IRI_PREFIX)

    @staticmethod
    def _is_cuds_iri_ontology(iri):
        for o in namespace_registry._graph.objects(URIRef(iri), RDF.type):
            if o in frozenset({OWL.DatatypeProperty,
                               OWL.ObjectProperty,
                               OWL.Class}):
                return False
        return True

    def _unreachable_warning(self, root_obj: UID):
        """Raises a warning when there are unreachable cuds.

        Gets a list of all the CUDS objects in the session which are
        unreachable from the specified `root_obj`. If there are any, then
        raises a warning that lists some of the unreachable CUDS objects.

        Args:
            root_obj (UID): The root object with respect to
                which objects are deemed reachable or unreachable.
        """
        unreachable = self._registry._get_not_reachable(root_obj, rel=None)
        max_cuds_on_warning = 5
        if len(unreachable) > 0:
            warning = "Some CUDS objects are unreachable " \
                      "from the wrapper object: " \
                      "{cuds}{more}." \
                      "\n" \
                      "If you want to be able to retrieve those CUDS " \
                      "objects later, either add them to the wrapper object " \
                      "or to any other CUDS that is reachable from it." \
                .format(cuds=', '.join(str(x) for x in itertools
                                       .islice(unreachable,
                                               max_cuds_on_warning)),
                        more=" and " + str(len(unreachable)
                                           - max_cuds_on_warning)
                             + " more" if len(unreachable) > 5
                        else "")
            logger.warning(warning)
