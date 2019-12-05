# Working with EMMO using OSP-core.

Follow these steps to use EMMO with OSP-core.

1. Clone the repo of EMMO:

   ```sh
   git clone https://github.com/emmo-repo/EMMO.git
   cd EMMO
   ```

2. Checkout the branch of choice:

    ```sh
    git checkout <branch_name>
    ```

3. Start Protege 5.2.0 with installed FaCT++ reasoner plugin

4. Open EMMO. For example open (File > Open...) the following file:
   - emmo/emmo_all.owl

5. Run the FaCT++ reasoner (Reasoner > FaCT++ | Reasoner > Start Reasoner)

6. Export the inferred Axioms (File > Export inferred axioms as ontology)

7. Convert the resulting owl file to YAML:

   ```sh
   owl2yml -n EMMO emmo_inferred.owl -c osp/core/tools/conversion_options/emmo.conversion_options.yml
   ```

8. Install the resulting YAML file:

   ```sh
   pico install ontology.emmo.yml
   ```

9. Start creating cuds objects. Check the getting-started repository in the SimPhoNy group.

   ```py
   >>> from osp.core import emmo
   >>> n = emmo.Number(value=1)
   >>> ...
   ```
