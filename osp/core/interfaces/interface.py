"""An Interface represents an interface between OSP-core and other software."""

from typing import Optional

from rdflib.term import Identifier


class Interface:
    """Class representing an interface between OSP-core and other software."""

    # Definition of:
    #   Interface
    # ↓ ---------- ↓

    root: Optional[Identifier] = None

    # ↑ ------------ ↑
    # Definition of:
    #   Interface
