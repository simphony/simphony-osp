import yaml
import sys
import owlready2
import re
import warnings
from collections import OrderedDict as odict


class OwlToYmlConverter():
    """Class that converts OWL ontologies to yml"""

    def __init__(self, owl_ontology_file, version="0.0.1"):
        """Initialize the converter

        :param owl_ontology_file: The owl file to convert
        :type owl_ontology_file: str
        """
        self.owl_onto = owlready2.get_ontology(owl_ontology_file)
        self.yaml_onto = odict()
        self.yaml_onto["VERSION"] = version
        self.cuds_onto = odict()
        self.cuds_onto["ENTITY"] = odict(
            definition="Root of all CUDS entities",
            subclass_of=list()
        )
        self.yaml_onto["CUDS_ONTOLOGY"] = self.cuds_onto

    def convert(self):
        """Perform the conversion"""
        self.owl_onto.load()
        for r in self.owl_onto.object_properties():
            self._add_relationship(r)

        for c in self.owl_onto.classes():
            self._add_class(c)

    def write(self, filename="ontology.yml"):
        """Write the yml ontology to disk"""
        Dumper = self._get_yml_dumper()
        with open(filename, "w") as f:
            s = yaml.dump(
                data=self.yaml_onto,
                Dumper=Dumper,
                default_flow_style=False,
                allow_unicode=True,
                explicit_start=True
            )
            # s = s.replace(r"\n", "\n      ")
            print(s, file=f)

    def _add_relationship(self, relationship):
        """ Add the given relationship to the yaml ontology

        :param relationship: The relationship to add.
        :type relationship: owlready2.ObjectPropertyClass
        """
        label = self._get_cuds_label(relationship)
        definition = self._get_definition(relationship)
        inverse = None
        if relationship.inverse_property:
            inverse = self._get_cuba_label(relationship.inverse_property)

        # get superclasses and characteristics
        superclasses = []
        characteristics = []
        for c in relationship.is_a:
            if c is owlready2.ObjectProperty:
                continue
            if isinstance(c, owlready2.ObjectPropertyClass):  # superclasses
                superclasses.append(
                    self._get_cuba_label(c)
                    if repr(c) != "owl.topObjectProperty"
                    else "CUBA.ENTITY"
                )
            elif repr(c).startswith("owl."):  # characteristics
                characteristics.append(repr(c)[4:-8].lower())
            elif isinstance(c, owlready2.Inverse):
                pass
            else:
                warnings.warn('omits %r for %r' % (c, label))

        domains = [self._parse_class_expression(ce)[1]
                   for ce in relationship.domain]
        ranges = [self._parse_class_expression(ce)[1]
                  for ce in relationship.range]

        # add it
        self.cuds_onto[label] = odict(
            definition=definition,
            inverse=inverse,
            subclass_of=superclasses,
            domain=self._restrictions_to_yml(domains),
            range=self._restrictions_to_yml(ranges),
            characteristics=characteristics
        )

    def _add_class(self, onto_class):
        """Add a class to the yaml ontology

        :param onto_class: The class to add.
        :type onto_class: owlready2.ThingClass
        """
        label = self._get_cuds_label(onto_class)
        definition = self._get_definition(onto_class)

        superclasses = []
        restrictions = []
        for ce in onto_class.is_a:
            is_superclass, parsed_ce = self._parse_class_expression(
                ce, restrictions
            )
            if is_superclass:
                superclasses.append(parsed_ce)
            elif parsed_ce is not None:
                restrictions.append(parsed_ce)

        equivalent_to = [self._parse_class_expression(ce)[1]
                         for ce in onto_class.equivalent_to]
        disjoints = [self._parse_class_expression(ce)[1]
                     for disjoint in onto_class.disjoints()
                     for ce in disjoint.entities
                     if ce != onto_class]

        self.cuds_onto[label] = odict(
            definition=definition,
            subclass_of=superclasses,
            equivalent_to=self._restrictions_to_yml(equivalent_to),
            restrictions=self._restrictions_to_yml(restrictions),
            disjoints=disjoints
        )

    def _parse_class_expression(self, ce, old_restrictions=None):
        """Parse class expressions

        :param ce: The class expression to parse
        :type ce: Union[owlready2.Restriction, owlready2.ClassConstruct,
                        owlready2.ThingClass]
        :param old_restrictions: The old restrictions.
            Used to merge some + only restrictions, defaults to None
        :type old_restrictions: dict(), optional
        :return: The parsed class expression
        :rtype: dict()
        """
        old_restrictions = old_restrictions or list()
        if ce is owlready2.Thing:
            return False, None
        if isinstance(ce, owlready2.ThingClass):
            return True, self._get_cuba_label(ce)
        elif isinstance(ce, owlready2.Restriction):
            return False, self._parse_restriction(ce, old_restrictions)
        elif isinstance(ce, owlready2.ClassConstruct):
            return False, self._parse_class_construct(ce)
        # TODO HasSelf

        warnings.warn('Unexpected class expression: %s' % type(ce))
        return False, None

    def _get_cuds_label(self, entity):
        """Returns CUDS label for entity (upper case)."""
        return self._get_label(entity).upper()

    def _get_cuba_label(self, entity):
        """Returns CUBA label for entity ("CUBA." prepended and upper case)."""
        return 'CUBA.' + self._get_label(entity).upper()

    def _get_label(self, entity):
        """Returns a label for entity."""
        if entity is owlready2.Nothing:
            label = 'Nothing'
        elif hasattr(entity, 'label') and entity.label:
            label = entity.label.first()
        elif isinstance(entity, owlready2.ClassConstruct):
            label = entity.__class__.__name__
        else:
            label = re.sub(r'^.*\.', '', repr(entity))
        label = label.replace(" ", "_")
        label = label.replace("-", "_")
        return str(label)

    def _get_definition(self, entity):
        """Returns definition for owl class or object property `entity` by
        combining its annotations."""
        if isinstance(entity, str):
            entity = self.owl_onto[entity]
        descr = []
        annotations = self._get_annotations(entity)
        if 'definition' in annotations:
            descr.extend(annotations['definition'])
        if 'elucication' in annotations and annotations['elucidation']:
            for e in annotations['elucidation']:
                descr.extend(['', 'ELUCIDATION:', e])
        if 'axiom' in annotations and annotations['axiom']:
            for e in annotations['axiom']:
                descr.extend(['', 'AXIOM:', e])
        if 'comment' in annotations and annotations['comment']:
            for e in annotations['comment']:
                descr.extend(['', 'COMMENT:', e])
        if 'example' in annotations and annotations['example']:
            for e in annotations['example']:
                descr.extend(['', 'EXAMPLE:', e])
        return '\n'.join(descr).strip()

    def _get_annotations(self, entity):
        """Get the annotations of an entity

        :param entity: The entity to get the annotations from.
        :type entity: owlready2.Entity
        :return: The annotations of the entity as a dict
        :rtype: dict
        """
        d = {'comment': entity.comment}
        for a in self.owl_onto.annotation_properties():
            d[a.label.first()] = [
                o.strip('"') for s, p, o in
                self.owl_onto.get_triples(entity.storid, a.storid, None)]
        return d

    def _parse_restriction(self, new_restriction, old_restrictions):
        relationship = self._get_cuba_label(new_restriction.property)
        _, target = self._parse_class_expression(new_restriction.value)
        rtype = owlready2.class_construct. \
            _restriction_type_2_label[new_restriction.type]

        # test of old restriction can be modified
        modify_restriction = None
        for restriction in old_restrictions:
            for key, value in restriction.items():
                if key == relationship and value["target"] == target:
                    modify_restriction = value
                    break
            else:
                continue
            break

        # Create a new restriction
        is_new = modify_restriction is None
        if modify_restriction is None:
            modify_restriction = odict(cardinality=[0, None],
                                       target=target,
                                       only=False)

        # Parse restriction and set cardinality accordingly
        cardinality = modify_restriction["cardinality"]
        if rtype == "exactly":
            cardinality[0] = new_restriction.cardinality
            cardinality[1] = new_restriction.cardinality
        elif rtype == "min":
            cardinality[0] = new_restriction.cardinality
        elif rtype == "max":
            cardinality[1] = new_restriction.cardinality
        elif rtype == "some":
            cardinality[0] = 1
        elif rtype == "only":
            modify_restriction["only"] = True
        else:
            raise ValueError("Unsupported restriction type %s"
                             % new_restriction)
        return odict({relationship: modify_restriction}) if is_new else None

    def _parse_class_construct(self, class_construct):
        """Parse a class construct (Union / Intersection / ...)

        :param class_construct: The class construct to parse
        :type class_construct: owlready2.ClassConstruct
        :return: The parsed class construct
        :rtype: Ordered dict
        """
        label = self._get_label(class_construct).upper()
        classes = class_construct.Classes \
            if hasattr(class_construct, "Classes") \
            else [class_construct.Class]

        parsed_ces = list()
        for ce in classes:
            _, parsed_ce = self._parse_class_expression(ce)
            parsed_ces.append(parsed_ce)
        return odict({label: parsed_ces})

    def _restrictions_to_yml(self, restrictions):
        """Convert the restriction tuples to a+ / a-b

        :param restrictions: The restrictions to convert
        :type restrictions: OrderedDict
        :return: The converted restrictions
        :rtype: OrderedDict
        """
        if isinstance(restrictions, list):
            for x in restrictions:
                self._restrictions_to_yml(x)
        if isinstance(restrictions, dict):
            for key, value in restrictions.items():
                if key == "cardinality" and value[1] is None:
                    restrictions["cardinality"] = "%s+" % value[0]
                elif key == "cardinality":
                    restrictions["cardinality"] = "%s-%s" % tuple(value)
                else:
                    self._restrictions_to_yml(value)
        return restrictions

    def _get_yml_dumper(self):
        """ Make sure YAML file is ordered"""

        # Try to use LibYAML bindings if possible
        # (Recipe copied from
        # https://gist.github.com/oglops/c70fb69eef42d40bed06)
        try:
            from yaml import CLoader as Loader, CDumper as Dumper
        except ImportError:
            from yaml import Loader, Dumper

        # YAML loader and dumper for ordered dicts
        def dict_representer(dumper, data):
            return dumper.represent_dict(data.items())

        def dict_constructor(loader, node):
            return odict(loader.construct_pairs(node))

        _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
        Loader.add_constructor(_mapping_tag, dict_constructor)
        Dumper.add_representer(odict, dict_representer)
        Dumper.add_representer(
            str, yaml.representer.SafeRepresenter.represent_str)
        Dumper.add_representer(
            type(None),
            lambda dumper, value: dumper.represent_scalar(
                u'tag:yaml.org,2002:null', '')
        )
        return Dumper


if __name__ == "__main__":
    owl_ontology_file = sys.argv[-1]
    converter = OwlToYmlConverter(owl_ontology_file)
    converter.convert()
    converter.write()
