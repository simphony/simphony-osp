"""Module aimed at providing an ontology lager on top of the RDF layer."""

from simphony_osp.session.session import Session, SessionSet

__all__ = ["Session", "SessionSet", "core_session"]

core_session = Session.get_default_session()
