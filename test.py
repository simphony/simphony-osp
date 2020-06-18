from osp.core.ontology import Parser
import rdflib
import logging

logging.getLogger("osp.core").setLevel(logging.INFO)
p = Parser(rdflib.Graph())
p.parse("osp/core/ontology/files/cuba.ontology.yml", "emmo.yml")