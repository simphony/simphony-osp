package org.simphony;

import static org.junit.Assert.assertTrue;

import org.junit.Test;

/**
 * Unit test for simple App.
 */
public class AppTest 
{
    /**
     * Rigorous Test :-)
     */
    @Test
    public void shouldAnswerWithTrue()
    {
        OntologyLoader.main(new String[]{"resources/foaf.rdf"});
        assertTrue( true );
    }
}
