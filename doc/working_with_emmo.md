# Working with EMMO using OSP-core.

Follow these steps to use EMMO with OSP-core.

1. Clone the repo of EMMO:

   ```sh
   git clone https://github.com/emmo-repo/EMMO.git
   cd EMMO
   ```

2. Checkout the newest branch (v0.9.9r2):

    ```sh
    git checkout v0.9.9r2
    ```

3. Start Protege 5.2.0 with installed FaCT++ reasoner plugin

4. Open EMMO. For example open (File > Open...) the following files one after the other in the same window.
   - emmo/emmo.owl
   - emmo/properties/emmo-properties.owl
   - emmo/examples/emmo-properties-examples.owl

5. Run the FaCT++ reasoner (Reasoner > FaCT++ | Reasoner > Start Reasoner)

6. Export the inferred Axioms (File > Export inferred axioms as ontology)

7. Convert the resulting owl file to YAML. This is explained in doc/conversion_owl_to_yaml.md.

8. Install osp-core with the resulting YAML file:

   ```sh
   python setup.py install -o ontology.emmo_inferred.yml
   ```

9. Start creating cuds objects. Check the getting-started repository in the SimPhoNy group.

   ```py
   >>> import cuds.classes
   >>> n = cuds.classes.Number(1)
   >>> ...
   ```
