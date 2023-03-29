"""Tests for the SimPhoNy OSP.

Brief summary of the contents of the module:

- `benchmark.py`: Defines an abstract class to base individual benchmarks on.
- `benchmark_api.py`: Benchmarks methods from SimPhoNy's public API. Currently
  exclusively focused on methods associated to ontology individuals.
- `pytest.ini`: pytest configuration (to run benchmarks only). Tests are run
  with unittest.
- `test_api.py`: Tests public API methods involving sessions, terminological
  knowledge, assertional knowledge, `pico`, and the `simphony_osp.tools`
  module. Check the docstring of each test case for more details.
- `test_api_importexport_*`: Files used by `test_apy.py` to test importing
  and exporting RDF files.
- `test_simphony_osp_session.py`: Tests functionality in the
  `simphony_osp.session` module that is not part of the public API.
- `test_wrapper.py`: End-to-end tests involving the wrappers included with
  SimPhoNy.
"""
