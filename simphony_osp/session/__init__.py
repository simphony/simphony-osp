"""Module aimed at providing an ontology lager on top of the RDF layer."""

from simphony_osp.session.session import Session

__all__ = ["Session", "core_session"]

core_session = Session.get_default_session()
