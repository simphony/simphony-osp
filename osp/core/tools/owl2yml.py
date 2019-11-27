import os
import re
import yaml
import owlready2
import argparse
import warnings
from collections import OrderedDict as odict
from functools import reduce
import operator


convert_special_chars = {
    "+": "_PLUS",
    "-": "_MINUS",
    "~": "_TILDE",
    ".": "_DOT"
}


class OwlToYmlConverter():
    """Class that converts OWL ontologies to yml"""

    def __init__(self, owl_ontology_file, conversion_options_file,
                 namespace, version):
        """Initialize the converter

        :param owl_ontology_file: The owl file to convert
        :type owl_ontology_file: str
        """
        self.owl_onto = owlready2.get_ontology(owl_ontology_file)
        self.yaml_onto = odict()
        self.yaml_onto["VERSION"] = self.version = version
        self.yaml_onto["NAMESPACE"] = self.namespace = namespace
        self.yaml_onto["ONTOLOGY"] = self.onto = odict()
        self.parsed_entities = set()

        self.conversion_options = None
        if conversion_options_file:
            with open(conversion_options_file, "r") as f:
                self.conversion_options = yaml.safe_load(f)

    def convert(self):
        """Perform the conversion"""
        self.owl_onto.load()
        for r in self.owl_onto.object_properties():
            self._add_relationship(r)

        for c in self.owl_onto.classes():
            self._add_class(c)

        self._apply_conversion_options()

    def _add_class(self, onto_class):
        """Add a class to the yaml ontology

        :param onto_class: The class to add.
        :type onto_class: owlready2.ThingClass
        """
        if onto_class in self.parsed_entities:
            return
        self.parsed_entities.add(onto_class)

        try:
            label = self._get_label(onto_class)
        except RuntimeError:
            return
        description = self._get_description(onto_class)

        # parse subclasses
        superclasses = self._parse_class_expressions(onto_class.is_a)
        equivalent_to = self._parse_class_expressions(onto_class.equivalent_to)

        # parse disjoint statements
        disjoints = list()  # disjoint all
        for disjoint in onto_class.disjoints():
            disjoints.extend(self._parse_class_expressions(
                [e for e in disjoint.entities if e != onto_class]
            ))
        for disjoint_union in onto_class.disjoint_unions:
            equivalent_to.append(self._parse_class_expressions(
                disjoint_union, combine_operator="OR"
            ))
            for entity in disjoint_union:  # disjoint union
                if entity not in self.parsed_entities:
                    self._add_class(entity)
                self.onto[self._get_label(entity)]["disjoint_with"].extend(
                    self._parse_class_expressions(
                        [x for x in disjoint_union if x != entity]
                    )
                )

        # add to the ontology
        self.onto[label] = odict(
            description=description,
            subclass_of=superclasses,
            equivalent_to=equivalent_to,
            disjoint_with=disjoints
        )

    def _add_relationship(self, relationship):
        """ Add the given relationship to the yaml ontology

        :param relationship: The relationship to add.
        :type relationship: owlready2.ObjectPropertyClass
        """
        if relationship in self.parsed_entities:
            return
        self.parsed_entities.add(relationship)

        try:
            label = self._get_label(relationship)
        except RuntimeError:
            return
        description = self._get_description(relationship)
        inverse = None
        if relationship.inverse_property:
            inverse = self._get_prefixed_label(relationship.inverse_property)

        # get superclasses and characteristics
        superclasses = []
        characteristics = []
        for c in relationship.is_a:
            if c is owlready2.ObjectProperty:
                continue
            if isinstance(c, owlready2.ObjectPropertyClass):  # superclasses
                superclasses.append(self._get_prefixed_label(c))
            elif repr(c).startswith("owl."):  # characteristics
                characteristics.append(repr(c)[4:-8].lower())
            elif isinstance(c, owlready2.Inverse):
                pass
            else:
                warnings.warn('omits %r for %r' % (c, label))

        domains = self._parse_class_expressions(relationship.domain,
                                                combine_operator="AND")
        ranges = self._parse_class_expressions(relationship.range,
                                               combine_operator="AND")

        # add it
        self.onto[label] = odict(
            description=description,
            subclass_of=superclasses,
            domain=domains,
            range=ranges,
            characteristics=characteristics
        )
        if inverse:
            self.onto[label]["inverse"] = inverse

    def _get_prefixed_label(self, entity, namespace=None):
        """Returns label with namespace for entity
        ("<NAMESPACE>." prepended and upper case)."""
        if entity is owlready2.Thing:
            return "CUBA.ENTITY"
        if entity is owlready2.Nothing:
            return "CUBA.NOTHING"
        if repr(entity) == "owl.topObjectProperty":
            return "CUBA.RELATIONSHIP"
        namespace = namespace or self.namespace
        label = self._get_label(entity)
        return '%s.%s' % (namespace, label)

    def _get_label(self, entity):
        """Returns a label for entity."""
        if entity in [owlready2.Nothing, owlready2.Thing]:
            raise RuntimeError("No non-prefixed label for %s !" % entity)
        if repr(entity) == "owl.topObjectProperty":
            raise RuntimeError("No non-prefixed label for %s !" % entity)
        if hasattr(entity, 'label') and entity.label:
            label = entity.label.first()
        elif isinstance(entity, owlready2.ClassConstruct):
            label = entity.__class__.__name__
        else:
            label = re.sub(r'^.*\.', '', repr(entity))
        label = label.replace(" ", "_")
        label = label.replace("-", "_")
        if re.compile(r"^\d").match(label):
            label = "_" + label
        for old, new in convert_special_chars.items():
            label = label.replace(old, new)
        label = str(label).upper()
        if not re.compile(r"(_|[A-Z])([A-Z]|[0-9]|_)*").match(label):
            raise ValueError("Invalid name %s." % label)
        return label

    def _get_description(self, entity):
        """Returns description for owl class or object property `entity` by
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

    def _parse_class_expressions(self, class_expressions, group_result=False,
                                 combine_operator=None):
        """Parse class expressions

        :param class_expressions: The class expression to parse
        :type class_expressions: Union[owlready2.Restriction,
                                       owlready2.ClassConstruct,
                                       owlready2.ThingClass]
        :return: The parsed class expression
        :rtype: dict()
        """
        class_names = list()
        rel_ces = dict()
        op_class_expressions = list()

        # Parse the class expression depending on the type of expression
        for ce in class_expressions:
            if ce is owlready2.Thing or isinstance(ce, owlready2.ThingClass):
                class_names.append(self._get_prefixed_label(ce))
            elif isinstance(ce, owlready2.Restriction):
                if isinstance(ce.property, owlready2.Inverse):
                    continue
                key = (ce.property, ce.value)
                if key not in rel_ces:
                    rel_ces[key] = list()
                rel_ces[key].append(ce)
            elif isinstance(ce, owlready2.ClassConstruct):
                op_class_expressions.append(
                    self._parse_op_class_expression(ce)
                )
        # TODO HasSelf

        # relationship class expressions have not been parsed yet.
        # Parse them now.
        rel_class_expressions = list()
        for (relationship, target), ces in rel_ces.items():
            rel_class_expressions.append(
                self._parse_rel_class_expressions(relationship, target, ces)
            )

        result = (class_names,
                  rel_class_expressions,
                  op_class_expressions)
        if group_result and combine_operator:
            return [{combine_operator: x} for x in result]
        if group_result:
            return result
        if combine_operator:
            return {combine_operator: reduce(operator.add, result)}
        return reduce(operator.add, result)

    def _parse_op_class_expression(self, class_expression):
        """Parse a class construct (Union / Intersection / ...)

        :param class_expression: The class construct to parse
        :type class_expression: owlready2.ClassConstruct
        :return: The parsed class construct
        :rtype: Ordered dict
        """
        label = self._get_label(class_expression)
        if hasattr(class_expression, "Classes"):
            classes = class_expression.Classes
            return self._parse_class_expressions(classes,
                                                 combine_operator=label)
        else:
            classes = [class_expression.Class]
            return {label: self._parse_class_expressions(classes)[0]}

    def _parse_rel_class_expressions(self, relationship, target, restrictions):
        """Parse a class expression describing the relationships of the class.

        :param relationship: The relationship the restriction is about.
        :type relationship: owlready2.ObjectProperty
        :param target: The class expression the class can be related with
        :type target: owlready2.ClassExpression
        :param restrictions: The class expressions/restrictions
        :type restrictions: owlready2.Restriction
        :raises ValueError: Unsupported restriction
        :return: The parsed expression
        :rtype: Dict[Str, Any]
        """
        relationship = self._get_prefixed_label(relationship)
        target = self._parse_class_expressions([target])[0]
        exclusive = False
        cardinality = [0, None]

        for restriction in restrictions:
            rtype = owlready2.class_construct. \
                _restriction_type_2_label[restriction.type]

            if rtype == "exactly":
                cardinality[0] = restriction.cardinality
                cardinality[1] = restriction.cardinality
            elif rtype == "min":
                cardinality[0] = restriction.cardinality
            elif rtype == "max":
                cardinality[1] = restriction.cardinality
            elif rtype == "some":
                cardinality[0] = 1
            elif rtype == "only":
                exclusive = True
            else:
                raise ValueError("Unsupported restriction type %s"
                                 % restriction)

        if cardinality[1] is None:
            cardinality = "%s+" % cardinality[0]
        else:
            cardinality = "%s-%s" % tuple(cardinality)
        return odict({relationship: odict(
            exclusive=exclusive,
            cardinality=cardinality,
            range=target
        )})

    def _apply_conversion_options(self):
        """Apply the conversion options"""
        if self.conversion_options is None:
            return
        if "default_rel" in self.conversion_options:
            entity = owlready2.IRIS[self.conversion_options["default_rel"]]
            label = self._get_label(entity)
            self.onto[label]["default_rel"] = True
        if "active_relationships" in self.conversion_options:
            for iri in self.conversion_options["active_relationships"]:
                entity = owlready2.IRIS[iri]
                label = self._get_label(entity)
                self.onto[label]["subclass_of"].append(
                    "CUBA.ACTIVE_RELATIONSHIP"
                )
        if "insert_entities" in self.conversion_options:
            self.onto.update(self.conversion_options["insert_entities"])
        if "update_entities" in self.conversion_options:
            update_entities = self.conversion_options["update_entities"]
            for key, value in update_entities.items():
                self.onto[key].update(value)

    def write(self, file="ontology.yml"):
        """Write the yml ontology to disk"""
        Dumper = self._get_yml_dumper()
        s = yaml.dump(
            data=self.yaml_onto,
            Dumper=Dumper,
            default_flow_style=False,
            allow_unicode=True,
            explicit_start=True
        )
        # s = s.replace(r"\n", "\n      ")

        if isinstance(file, str):
            with open(file, "w") as f:
                print(s, file=f)
        else:
            print(s, file=file)

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


def run_from_terminal():
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Convert an ontology in OWL format to "
                    "an ontology in YAML format."
    )
    parser.add_argument("input_file", metavar="input-file",
                        type=os.path.abspath,
                        help="The path to the input owl file")
    parser.add_argument("--namespace", "-n",
                        type=str.upper, required=True,
                        help="The namespace for the resulting YAML file "
                        "in UPPERCASE")
    parser.add_argument("--conversion-options-file", "-c",
                        type=str, default=None,
                        help="Path to a file explaining how the ontology "
                             "should be transformed, s.t. it is compatible "
                             "with osp-core")
    parser.add_argument("--version", "-v",
                        type=str, default="0.0.1",
                        help="The version string for the resulting YAML file")
    parser.add_argument("--output-file", "-o",
                        type=os.path.abspath, default=None,
                        help="Where the output file should be saved")
    args = parser.parse_args()

    # Convert the OWL file to a YAML file
    converter = OwlToYmlConverter(
        owl_ontology_file=args.input_file,
        conversion_options_file=args.conversion_options_file,
        namespace=args.namespace,
        version=args.version
    )
    converter.convert()
    output_filename = args.output_file or os.path.abspath(
        "ontology.%s.yml" % os.path.basename(args.input_file)[:-4]
    )
    converter.write(file=output_filename)


if __name__ == "__main__":
    run_from_terminal()
