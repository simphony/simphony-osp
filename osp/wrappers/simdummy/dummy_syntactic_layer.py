"""A dummy simulation backend used for demonstrational and testing purposes.

With each simulation step, the age of all person that are direct
descendents of the Wrapper object will be increased by one.
Each simulation step one person will move to the city and become
an inhabitant.
"""


class DummyPerson:
    """A Person in the simulation."""

    def __init__(self, name, age):
        """Initialize the person.

        Args:
            name (str): The name of the person
            age (int): The age of the person.
        """
        self.name = name
        self.age = age

    def get_older(self, num_years):
        """Increase the age by the given number of years.

        Args:
            num_years (int): The number of years the person aged.
        """
        self.age += num_years


class DummySyntacticLayer:
    """A dummy simulation backend used for testing purposes."""

    def __init__(self):
        """Initialize the dummy syntactic layer."""
        self.persons = list()
        self.i = 0

    def add_person(self, person):
        """Add a person to the backend.

        Args:
            person (DummyPerson): The person to add to the backend.

        Returns:
            int: The index of the added person.
        """
        self.persons.append(person)
        return len(self.persons) - 1

    def get_person(self, idx):
        """Get a person by index.

        Args:
            idx (int): The index of the person to get.

        Returns:
            Tuple[bool, Person]: Whether the person already moved to the city
                and the person object.
        """
        return idx < self.i, self.persons[idx]

    def simulate(self, numSteps):
        """Simulate the persons for the given number of steps.

        Args:
            numSteps (int): The number of years to simulate.
        """
        self.i += numSteps

        for p in self.persons:
            p.get_older(numSteps)
