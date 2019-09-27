# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import argparse
import os.path
import re
import textwrap
from string import Template

from cuds.generator.validity_checker import ValidityChecker
from cuds.generator.parser import Parser
from cuds.utils import format_class_name


class ClassGenerator(object):
    """
    Handles the generation of the python classes and other support files from
    the given yaml ontology using a template file.
    """
    # Default root for not instantiable attributes
    ROOT_NOT_CLASSES = "VALUE"
    # Default root of all relationship classes
    ROOT_RELATIONSHIP = "RELATIONSHIP"
    # Default root of all active relationship classes
    ROOT_ACTIVE_RELATIONSHIP = "ACTIVE_RELATIONSHIP"
    # Default root of all passive relationship classes
    ROOT_PASSIVE_RELATIONSHIP = "PASSIVE_RELATIONSHIP"
    # Key for the default value in the ontology
    DEFAULT_ATTRIBUTE_KEY = "default"
    # Key for the inverse of relationships
    INVERSE_ATTRIBUTE_KEY = "inverse"
    # Attribute specifying the default relationship of the ontology
    DEFAULT_REL_ATTRIBUTE_KEY = "default_rel"

    def __init__(self, yaml_filename, entity_template, relationship_template,
                 output_folder):
        """
        Constructor. Sets the filenames and creates the parser.

        :param yaml_filename: File with the ontology
        :param entity_template: File with the structure of the entities
        :param relationship_template:
        File with the structure of the relationships
        :param output_folder: Folder for the generated classes
        """
        self._yaml_filename = yaml_filename
        self._entity_template = self._get_template(entity_template)
        self._relationship_template = self._get_template(relationship_template)
        self._parser = Parser(self._yaml_filename)
        self._checker = ValidityChecker(self._parser, self)
        self._checker.check_and_repair()
        self._default_relationship = self._checker.default_relationship
        self._output_folder = output_folder

        # Don't create classes from ROOT_NOT_CLASSES and its descendants
        not_classes = self._parser.get_descendants(self.ROOT_NOT_CLASSES)
        not_classes.append(self.ROOT_NOT_CLASSES)
        self._not_classes = {c: self._parser.get_datatype(c)
                             for c in not_classes}

        relationships = self._parser.get_descendants(self.ROOT_RELATIONSHIP)
        relationships.append(self.ROOT_RELATIONSHIP)
        self._relationships = set(relationships)

        # Create an instance for efficiency
        self._text_wrapper = textwrap.TextWrapper()

    def generate_classes(self):
        """
        Generates each individual class file and the CUBA enum file.
        """
        self._generate_init_file()
        self._generate_cuba_enum_file()
        self._generate_cuba_mapping()
        for entity in self._parser.get_entities():
            if entity not in self._not_classes:
                print("Generating {}".format(entity))
                self._generate_class_file(entity)
        self._add_settings_to_init_file()

    def _generate_init_file(self):
        """
        Generates the __init__ file in the cuds folder.
        """
        init_filename = os.path.join(self._output_folder, "__init__.py")

        with open(init_filename, 'w') as f:
            f.write("from .cuba import CUBA\n")
            f.close()

    def _generate_cuba_enum_file(self):
        """
        Generates the enum with the entities from the ontology.
        """
        cuba_filename = os.path.join(self._output_folder, "cuba.py")
        enum = "from enum import Enum, unique\n\n" \
               + "\n@unique\n" \
               + "class CUBA(Enum):\n"
        for element in self._parser.get_entities():
            enum += "    " + element + " = \"" + element + "\"\n"

        with open(cuba_filename, 'w+') as f:
            f.write(enum)
            f.close()

    def _generate_cuba_mapping(self):
        cuba_mapping_filename = os.path.join(self._output_folder,
                                             "cuba_mapping.py")
        file_content = "from .cuba import CUBA\n"
        elements = set(self._parser.get_entities()) - self._not_classes.keys()
        for element in elements:
            file_content += "from .%s import %s\n" % (
                element.lower(), format_class_name(element))
        file_content += "\n\nCUBA_MAPPING = {\n"
        for element in elements:
            file_content += "    CUBA.%s: %s, \n" % (
                element, format_class_name(element))
        file_content += "}\n"

        with open(cuba_mapping_filename, "w") as f:
            f.write(file_content)
            f.close()

    def _add_settings_to_init_file(self):
        """ Add the parsed settings to the init file
        """
        init_filename = os.path.join(self._output_folder, "__init__.py")
        settings = self._parser.get_parsed_settings()
        if self._default_relationship:
            settings.update({"default_relationship":
                             self._default_relationship})

        with open(init_filename, 'a+') as f:
            f.write("\nPARSED_SETTINGS = %s" % settings)
            f.close()

    def _generate_class_file(self, original_class):
        """
        Creates a class file using the template.

        :param original_class: uppercase name of the entity
        """
        # Get the parent
        parent = self._parser.get_parent(original_class)
        if parent == "":
            parent_module = "cuds.classes.cuds"
            parent_class = "Cuds"
        elif original_class == "RELATIONSHIP":
            parent_module = "builtins"
            parent_class = "object"
        else:
            parent_module = "." + parent.lower()
            parent_class = format_class_name(parent)

        definition = self._get_definition(original_class)
        fixed_class_name = format_class_name(original_class)

        content = {
            'class': fixed_class_name,
            'cuba_key': original_class,
            'definition': definition,
            'parent': parent_class,
            'parent_module': parent_module,
        }

        module = original_class.lower()

        # Get the relationship specific values
        if original_class in self._relationships:
            relationship_content = self._generate_relationship(original_class)
            content.update(relationship_content)
            self._write_content_to_template_file(content,
                                                 self._relationship_template,
                                                 module)
        # Get the entity specific values
        else:
            entity_content = self._generate_entity(original_class)
            content.update(entity_content)
            self._write_content_to_template_file(content,
                                                 self._entity_template,
                                                 module)

        self._add_class_import_to_init(module, fixed_class_name)

    def _get_definition(self, original_class):
        """
        Extracts and formats the definition from the parser.

        :param original_class: name of the ontology class
        """
        definition = self._parser.get_definition(original_class)
        # Wraps the text to 70 characters
        definition = self._text_wrapper.fill(definition)
        # Add indentation to the new lines
        return definition.replace("\n", "\n    ")

    def _generate_relationship(self, relationship_name):
        """
        Defines the value for the relationship only tokens.

        :param relationship_name: name of the relationship
        :return: dictionary with the content for the template
        """
        inverse_relationship = self._parser.get_value(relationship_name,
                                                      'inverse')

        content = {
            'inverse': inverse_relationship,
        }
        return content

    def _generate_entity(self, entity_name):
        """
        Defines the value for the entity only tokens.

        :param entity_name: name of the entity
        :return: dictionary with the content for the template
        """

        arguments_init, attr_sent_super, attr_initialised, \
            properties = self._get_constructor_attributes(entity_name)

        # Extract the relationships from the ontology
        relationships = self._parser.\
            get_cuba_attributes_filtering(entity_name,
                                          self._not_classes.keys())

        str_relationships = re.sub("'(CUBA.[A-Z_]*)'",
                                   r"\g<1>",
                                   str(relationships))

        content = {
            'arguments_init': arguments_init,
            'attributes_sent_super': attr_sent_super,
            'attributes_initialised': attr_initialised,
            'properties': properties,
            'relationships': str_relationships,
        }
        return content

    def _get_constructor_attributes(self, cuba_key):
        """
        Returns the attributes (own and inherited) used in the constructor.

        :param cuba_key: key of the entity
        :return: string_init: str all attributes
                 string_super: str inherited attributes
                 string_self: str own, not inherited attributes
        """

        all_attr = self._parser.get_attributes(cuba_key)
        # Inherited attributes are sent to parent constructor
        inherited_attr = set(self._parser.get_inherited_attributes(cuba_key))
        # Own attributes are set in the constructor
        own_attr = set(self._parser.get_own_attributes(cuba_key))

        list_init = ["self"]
        list_init_default = []
        list_super = []
        # Initialise with empty string to add indentation to first element
        list_self = []
        list_properties = []

        for name, properties in sorted(all_attr.items()):
            # Check that they are not instantiable classes
            if name.upper() in self._not_classes:
                datatype = self._not_classes[name.upper()]
                annotation = ":'%s'" % datatype
                # Default value
                if properties is not None and \
                        self.DEFAULT_ATTRIBUTE_KEY in properties:
                    default = properties[self.DEFAULT_ATTRIBUTE_KEY]
                    if isinstance(default, str):
                        list_init_default.append("%s%s='%s'" % (name,
                                                                annotation,
                                                                default))
                    else:
                        list_init_default.append("%s%s='%s'" % (name,
                                                                annotation,
                                                                default))
                # No default value
                else:
                    list_init.append(name + annotation)
                # Inherited properties go to supper
                if name in inherited_attr:
                    list_super.append(name + ", ")
                elif name == "session" and name in own_attr:
                    list_properties.append((name, datatype))
                    # list_self.append("if session.root is not None:")  TODO
                    # list_self.append("raise ValueError('The given session "
                    #                  "is already used in another wrapper')")
                    list_self.append("self._session = session")
                elif name in own_attr:
                    list_properties.append((name, datatype))
                    list_self.append("self._%s = convert_to(%s, '%s')"
                                     % (name, name, datatype))

        # Add default parameters at the end
        list_init += list_init_default

        string_init = ", ".join(list_init)
        string_super = "".join(list_super)
        string_self = "        " + "\n        ".join(list_self)
        string_property = self.get_property_string(list_properties)

        if list_self:
            string_self += "\n"

        return string_init, string_super, string_self, string_property

    def get_property_string(self, property_list):
        result = ""
        for p, datatype in property_list:
            getter = ["@property",
                      "def %s(self):" % p,
                      "    self._session._notify_read(self)",
                      "    return self._%s\n" % p]
            setter = ["@%s.setter" % p,
                      "def %s(self, x):" % p,
                      "    self.session._notify_read(self)",
                      "    self._%s = convert_to(x, \"%s\")"
                      % (p, datatype),
                      "    self.session._notify_update(self)\n\n"]
            funcs = getter + setter if p != "session" \
                else getter[0:2] + getter[3:]
            result += "\n".join(map(lambda x: "    " + x, funcs))
        return result

    def _write_content_to_template_file(self, content, template, class_file):
        """
        Writes the content of the class to a python file.

        :param content: dictionary with the values for the template's keywords
        :param template: instance of the template to fill in
        :param class_file: name of the class file
        """
        # Replace template tokens with specific values
        text = template.safe_substitute(content)

        # Create file from template substitutions
        filename = os.path.join(self._output_folder, class_file + ".py")
        with open(filename, 'w') as f:
            f.write(text)
            f.close()

    def _add_class_import_to_init(self, module_name, class_name):
        """
        Adds the import to the init file.

        :param module_name: name of the class file (module)
        :param class_name: name of the class
        """
        init_file = os.path.join(self._output_folder, "__init__.py")
        with open(init_file, 'a+') as f:
            f.write("from ." + module_name + " import " + class_name + "\n")
            f.close()

    @staticmethod
    def _get_template(template_file):
        """
        Opens the template file and reads its content.
        """
        with open(template_file, 'r') as f:
            template = f.read()
            f.close()
        return Template(template)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("YAML_file",
                            help="Input YAML file")
    arg_parser.add_argument("entity_template",
                            help="Template for the entities")
    arg_parser.add_argument("relationship_template",
                            help="Template for the relationships")
    arg_parser.add_argument("output_folder",
                            help="Root folder for the generated files")
    args = arg_parser.parse_args()

    generator = ClassGenerator(args.YAML_file,
                               args.entity_template,
                               args.relationship_template,
                               args.output_folder)
    generator.generate_classes()


if __name__ == "__main__":
    main()
