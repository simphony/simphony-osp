package org.simphony;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.logging.Logger;

import org.semanticweb.HermiT.ReasonerFactory;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.formats.RDFXMLDocumentFormat;
import org.semanticweb.owlapi.model.IRI;
import org.semanticweb.owlapi.model.OWLAxiom;
import org.semanticweb.owlapi.model.OWLDataFactory;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyCreationException;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.model.OWLOntologyStorageException;
import org.semanticweb.owlapi.reasoner.InferenceType;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.reasoner.OWLReasonerFactory;
import org.semanticweb.owlapi.util.InferredAxiomGenerator;
import org.semanticweb.owlapi.util.InferredOntologyGenerator;
import org.semanticweb.owlapi.util.InferredSubClassAxiomGenerator;
import org.semanticweb.owlapi.util.OWLOntologyMerger;

/**
 * Hello world!
 *
 */
public class OntologyLoader {
    private final static Logger LOGGER = Logger.getLogger(OntologyLoader.class.getName());

    public static void main(String[] args) {
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        OWLDataFactory df = manager.getOWLDataFactory();

        for (String arg : args) {
            try {
                manager.loadOntologyFromOntologyDocument(new File(arg));
            } catch (OWLOntologyCreationException e) {
                e.printStackTrace();
                LOGGER.warning("Could not load " + arg);
            }
        }
        try {
            File output = File.createTempFile("inferred_ontology", ".owl");
            IRI ontologyIRI = IRI.create(output);
            OWLOntologyMerger merger = new OWLOntologyMerger(manager);
            OWLOntology ontology = merger.createMergedOntology(manager, ontologyIRI);

            OWLReasonerFactory rf = new ReasonerFactory();
            OWLReasoner reasoner = rf.createReasoner(ontology);
            List<InferredAxiomGenerator<? extends OWLAxiom>> gens = new ArrayList<>();
            gens.add(new InferredSubClassAxiomGenerator());
            InferredOntologyGenerator iog = new InferredOntologyGenerator(reasoner, gens);
            iog.fillOntology(df, ontology);

            manager.saveOntology(ontology, new RDFXMLDocumentFormat());
        } catch (OWLOntologyStorageException | OWLOntologyCreationException | IOException e) {
            e.printStackTrace();
            LOGGER.warning("Could not store ontology ");
        }
    }
}
