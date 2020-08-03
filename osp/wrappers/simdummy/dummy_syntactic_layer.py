class DummyPerson():

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_older(self, num_years):
        self.age += num_years


class DummySyntacticLayer():
    def __init__(self):
        self.persons = list()
        self.i = 0

    def add_person(self, person):
        self.persons.append(person)
        return len(self.persons) - 1

    def get_person(self, idx):
        return idx < self.i, self.persons[idx]

    def simulate(self, numSteps):
        self.i += numSteps

        for p in self.persons:
            p.get_older(numSteps)
