import yaml
import os
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
        self.yaml_onto["ONTOLOGY_MODE"] = "minimum_requirements"
        self.class_onto = odict()
        self.yaml_onto["CUDS_ONTOLOGY"] = odict(
            ENTITY=odict(
                definition="Root of all CUDS entities",
                parent=None
            ),
            NOTHING=odict(
                definition="Nothing",
                parent="CUBA.ENTITY"
            ),
            VALUE=odict(
                definition="The root of all values",
                parent="CUBA.ENTITY"
            )
        )
        self.rel_onto = odict(
            RELATIONSHIP=odict(
                definition="Root of all relationships",
                parent="CUBA.ENTITY"
            ) ,
            IS_A=odict(
                definition="Secondary parents",
                parent="CUBA.RELATIONSHIP",
                inverse="CUBA.SUPERCLASS_OF"
            ),
            SUPERCLASS_OF=odict(
                definition="Inverse of CUBA.IS_A",
                parent="CUBA.RELATIONSHIP",
                inverse="CUBA.IS_A"
            )
        )
        self.class_onto = self.yaml_onto["CUDS_ONTOLOGY"]

    def print_warning(self):
        print("")
        print("Converting OWL ontology to YAML ontology...")
        print("Note that the current version of osp-core does not support "
              "every OWL ontology.")
        print("Therefore, the user has to make some decisions in order to "
              "convert the ontology.")
        print("Make sure you are aware of the current constraints of "
              "a YAML ontology (See doc/conversion_owl_to_yaml.md and "
              "doc/yaml_spec.md).")
        print("OSP-core will fully support EMMO and other OWL ontologies "
              "very soon!")
        print()
        print("For example: In OWL it is common that an entity can "
              "have multiple parents. OSP-core currently only allows a single "
              "parent. This will be changed in the upcoming days.")
        input("Press ENTER to continue! ")

    def convert(self):
        """Perform the conversion"""
        self.owl_onto.load()
        for r in self.owl_onto.object_properties():
            self._add_relationship(r)

        for c in self.owl_onto.classes():
            self._add_class(c)

        self._inject_obligatory_entity("ACTIVE_RELATIONSHIP",
                                       self.rel_onto,
                                       inverse="PASSIVE_RELATIONSHIP")
        self._inject_arguments()
        self._add_missing_inverses()
        self._resolve_duplicates()
        default_rel = self._input_cuds_label("Default relationship: ")
        self.rel_onto[default_rel]["default_rel"] = True
        self.yaml_onto["CUDS_ONTOLOGY"].update(self.rel_onto)
        self.yaml_onto["CUDS_ONTOLOGY"].update(self.class_onto)

    def _inject_arguments(self):
        """Inject children of CUBA.VALUE that will be arguments of
        the cuds classes"""
        arguments = dict()
        while True:
            name = self._input_cuds_label(
                "Enter classes that should have arguments: "
            )
            if not name:
                break
            while True:
                arg = self._input_cuds_label("argument name: ")
                if not arg:
                    break
                datatype = arguments.get(arg) or input("datatype: ")
                arguments[arg] = datatype
                assert arg not in self.class_onto, \
                    "Argument must not be in the ontology"
                self.class_onto[name]["CUBA." + arg] = None

        for arg, datatype in arguments.items():
            self.class_onto[arg] = odict(
                definition="",
                parent="CUBA.VALUE",
                datatype=datatype.upper()
            )

    def _resolve_duplicates(self):
        """Resolve duplicates by renaming"""
        duplicates = set(self.rel_onto.keys()) & set(self.class_onto.keys())
        for duplicate in duplicates:
            rename_type = self._user_choice(
                ["class", "relationship"],
                "%s has been specified as class and relationship. "
                "Which one do you want to rename?" % duplicate
            )
            rename_name = self._input_cuds_label("Rename to: ")
            rename_onto = self.rel_onto if rename_type == "relationship" \
                else self.class_onto
            self._rename_entity_recursively(
                rename_onto, duplicate, rename_name
            )

    def _add_missing_inverses(self):
        """ Add the missing inverse relationships"""
        print()
        print("OSP-core currently does not allow missing inverses. "
              "Please specify an inverse for every relationship. "
              "Each specified inverse must be in the ontology. "
              "Specifying an inverse for every entity will not be "
              "necessary in upcoming osp-core versions.")
        no_inverse = [entity
                      for entity, entity_def in self.rel_onto.items()
                      if "inverse" in entity_def
                      and entity_def["inverse"] is None]
        for entity in no_inverse:
            inverse = self._input_cuds_label(
                "Specify inverse of %s: " % entity
            )
            assert inverse in self.rel_onto, \
                "Specify an entity that is in the ontology"
            self.rel_onto[entity]["inverse"] = "CUBA." + inverse
        self.rel_onto["RELATIONSHIP"]["inverse"] = None

    def _inject_obligatory_entity(self, to_inject, onto, inverse=None,
                                  child=None):
        """Inject entities that must be present in yml ontologies.

        :param to_inject: The entity to inject
        :type to_inject: str
        :param onto: The ontology to inject it in
        :type onto: OrderedDict
        :param inverse: If given, inject given inverse as well,
            defaults to None
        :type inverse: str, optional
        :param child: The direct child of the injected class.
            User will be asked if not given, defaults to None
        :type child: str, optional
        """
        if child is None:
            print()
            print("OSP-core does currently have some requirements "
                  "in the ontology. There are some entities which must "
                  "be in the ontology. Please specify where to put "
                  "these obligatory entities in the ontology. "
                  "These constraints will "
                  "be relaxed very soon.")
        if to_inject not in onto:
            if child is None:
                print("\nNo CUBA.%s in the ontology." % to_inject)
                print("Specify the entity, that should "
                      "have %s as parent:" % to_inject)
                child = self._input_cuds_label("> ")
            parent = onto[child]["parent"]
            onto[to_inject] = odict(
                definition=None,
                parent=parent
            )
            onto[child]["parent"] = "CUBA.%s" % to_inject
            if inverse is not None:
                onto[to_inject]["inverse"] = "CUBA." + inverse
                self._inject_obligatory_entity(
                    to_inject=inverse,
                    onto=onto,
                    inverse=to_inject,
                    child=onto[child]["inverse"].replace("CUBA.", "")
                )

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

        # get parents and characteristics
        parents = []
        characteristics = []
        for c in relationship.is_a:
            if c is owlready2.ObjectProperty:
                continue
            if isinstance(c, owlready2.ObjectPropertyClass):  # parents
                parents.append(
                    self._get_cuba_label(c)
                    if repr(c) != "owl.topObjectProperty"
                    else "CUBA.RELATIONSHIP"
                )
            elif repr(c).startswith("owl."):  # characteristics
                characteristics.append(repr(c)[4:-8].lower())
            elif isinstance(c, owlready2.Inverse):
                pass
            else:
                warnings.warn('omits %r for %r' % (c, label))

        parent = self._user_choice(parents,
                                   "Choose the parent of %s. "
                                   % label)

        # add it
        self.rel_onto[label] = odict(
            definition=definition,
            inverse=inverse,
            parent=parent
        )

    def _add_class(self, onto_class):
        """Add a class to the yaml ontology

        :param onto_class: The class to add.
        :type onto_class: owlready2.ThingClass
        """
        label = self._get_cuds_label(onto_class)
        definition = self._get_definition(onto_class)

        parents = []
        restrictions = odict()
        for ce in onto_class.is_a:
            is_parent, parsed_ce = self._parse_class_expression(ce,
                                                                restrictions)
            if is_parent:
                parents.append(parsed_ce)
            elif parsed_ce is not None:
                restrictions.update(parsed_ce)

        parent = self._user_choice(parents,
                                   "Choose the primary parent of %s. "
                                   "The others will be related by CUBA.IS_A."
                                   % label,
                                   "CUBA.ENTITY")
        if len(parents) > 1:
            secondary_parents = set(parents) - {parent}
            restrictions.update({
                "CUBA.IS_A": odict({p: odict(cardinality=(1, 1))})
                for p in secondary_parents
            })
        self.class_onto[label] = odict(
            definition=definition,
            parent=parent,
            **self._restrictions_to_yml(restrictions),
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
        old_restrictions = old_restrictions or odict()
        if ce is owlready2.Thing:
            return True, "CUBA.ENTITY"
        if isinstance(ce, owlready2.ThingClass):
            return True, self._get_cuba_label(ce)
        elif isinstance(ce, owlready2.Restriction):
            return False, self._parse_restriction(ce, old_restrictions)

        warnings.warn('Unexpected class expression: %s' % type(ce))
        warnings.warn("OSP-core will support that very soon!")
        return False, None

    def _get_cuds_label(self, entity):
        """Returns CUDS label for entity (upper case)."""
        return self._to_cuds_label(self._get_label(entity))

    def _get_cuba_label(self, entity):
        """Returns CUBA label for entity ("CUBA." prepended and upper case)."""
        return 'CUBA.' + self._to_cuds_label(self._get_label(entity))

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
        return str(label)

    def _input_cuds_label(self, msg):
        """Let the user input a cuds label

        :param msg: The message to show the user.
        :type msg: str
        :return: The cuds label the user typed in.
        :rtype: str
        """
        x = input(msg)
        return self._to_cuds_label(x)

    def _to_cuds_label(self, label):
        """Convert a label to cuds label.

        :param label: The label to convert.
        :type label: str
        :return: The converted label.
        :rtype: str
        """
        if label.startswith("CUBA."):
            label = label[5:]
        label = label.upper()
        label = label.replace(" ", "_")
        label = label.replace("-", "_")
        return label

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
        """Parse an owl restriction and convert it to YAML.
        Will modify old_restrictions the new restriction is already present.

        :param new_restriction: The new owl restrictions to add
        :type new_restriction: owlready2.restriction
        :param old_restrictions: The parsed old restrictions
        :type old_restrictions: dict
        :return: The parsed restriction, if it was not
            contained in old_restrictions
        :rtype: Optional[Dict]
        """
        relationship = self._get_cuba_label(new_restriction.property)
        is_simple, target = self._parse_class_expression(new_restriction.value)
        if not is_simple:
            return
        rtype = owlready2.class_construct. \
            _restriction_type_2_label[new_restriction.type]

        # test of old restriction can be modified
        modify_restriction = None
        for restriction_rel, restriction in old_restrictions.items():
            for restriction_target, restriction_options in restriction.items():
                if restriction_rel == relationship \
                        and restriction_target == target:
                    modify_restriction = restriction_options
                    break
            else:
                continue
            break

        # Create a new restriction
        is_new = modify_restriction is None
        if modify_restriction is None:
            modify_restriction = odict({target: odict(cardinality=[0, None])})

        # Parse restriction and set cardinality accordingly
        cardinality = modify_restriction[target]["cardinality"]
        if rtype == "exactly":
            cardinality[0] = new_restriction.cardinality
            cardinality[1] = new_restriction.cardinality
        elif rtype == "min":
            cardinality[0] = new_restriction.cardinality
        elif rtype == "max":
            cardinality[1] = new_restriction.cardinality
        elif rtype == "some":
            cardinality[0] = 1

        return odict({relationship: modify_restriction}) if is_new else None

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

    def _rename_entity_recursively(self, sub_onto, old_name,
                                   new_name, prefix=""):
        """Rename an entity recursively.

        :param sub_onto: The (part of an) ontology where
            the entity should be renamed.
        :type sub_onto: Union[Dict, List, str]
        :param old_name: The entities old name
        :type old_name: str
        :param new_name: The entities new name
        :type new_name: str
        :param prefix: The prefix for the names, defaults to ""
        :type prefix: str, optional
        """
        if isinstance(sub_onto, list):
            for x in sub_onto:
                self._rename_entity_recursively(
                    x, old_name, new_name, prefix="CUBA."
                )
        if isinstance(sub_onto, dict):
            if prefix + old_name in sub_onto.keys():
                sub_onto[prefix + new_name] = sub_onto[prefix + old_name]
                del sub_onto[prefix + old_name]
            for key in sub_onto.keys():
                if sub_onto[key] == prefix + old_name:
                    sub_onto[key] = prefix + new_name
                else:
                    self._rename_entity_recursively(
                        sub_onto[key], old_name, new_name, prefix="CUBA."
                    )

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

    def _user_choice(self, items, prompt_msg, fallback=None):
        """Let the user choose which item is the correct one.

        :param items: A list of items to choose from
        :type items: list[Any]
        :param prompt_msg: The message to display the user.
        :type prompt_msg: str
        :param fallback: The object that will be returned if items is empty,
            defaults to None
        :type fallback: Any, optional
        :return: The chosen item
        :rtype: Any
        """
        if not items:
            return fallback
        if len(items) == 1:
            return items[0]
        print()
        print("A choice has to be made by the user. ")
        print("In the very near future osp-core will fully support "
              "OWL ontologies. Then no user choices will be required.")
        print()
        print(prompt_msg)
        for i, item in enumerate(items):
            print("%s)" % (i + 1), item)
        choice = input("Type the number of your choice: ")
        choice = int(choice) - 1
        return items[choice]


if __name__ == "__main__":
    owl_ontology_file = sys.argv[-1]
    name = os.path.splitext(os.path.basename(owl_ontology_file))[0]
    converter = OwlToYmlConverter(owl_ontology_file)
    converter.print_warning()
    converter.convert()
    converter.write("ontology.%s.yml" % name)
