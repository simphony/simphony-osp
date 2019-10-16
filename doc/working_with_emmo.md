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

3. Start Protege Version 5.2.0 with installed FaCT++ reasoner

4. Open (File > Open...) the following files one after the other in the same window.
   - emmo/emmo.owl
   - properties/emmo-properties.owl
   - examples/emmo-properties-examples.owl

5. Run the FaCT++ reasoner (Reasoner > FaCT++ | Reasoner > Start Reasoner)

6. Export the inferred Axioms (File > Export inferred axioms as ontology)

7. Convert the resulting owl file to YAML. This is explained in doc/conversion_owl_to_yaml.md.

8. Install osp-core with the resulting YAML file:

   ```sh
   python setup.py install -o ontology.yml
   ```
