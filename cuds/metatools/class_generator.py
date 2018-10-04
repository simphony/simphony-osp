import argparse
import os.path

from cuds.ontology.tools.parser import Parser
from cuds.utils import format_class_name
from string import Template
from textwrap import fill


class ClassGenerator(object):
    """
    Handles the generation of the python classes and other support files from
    the given yaml ontology using a template file.
    """

    def __init__(self, yaml_filename, template_filename, output_folder):
        """
        Constructor. Sets the filenames and creates the parser.

        :param yaml_filename: File with the ontology
        :param template_filename: File with the structure of the classes
        :param output_folder: Folder for the generated classes
        """
        self._yaml_filename = yaml_filename
        self._template_filename = template_filename
        self._template = None
        self._parser = Parser(self._yaml_filename)
        # Don't create classes from CUBA.VALUE and its descendants
        self.not_instantiable = set(self._parser.get_descendants("VALUE"))
        self.output_folder = output_folder

    def generate_classes(self):
        """
        Generates each individual class file and the CUBA enum file.
        """
        self._generate_attributes_file()
        self._generate_init_file()
        self._generate_enum_file()
        self._generate_template_instance()
        for entity in self._parser.get_entities():
            if entity not in self.not_instantiable:
                print("Generating {}".format(entity))
                self._generate_class_file(entity)

    def _generate_attributes_file(self):
        """
        Generates a file with all the attributes from the generated cuds.
        """
        filename = os.path.join(os.path.dirname(self.output_folder),
                                "all_cuds_attributes.py")
        attributes = self.not_instantiable.union({"name", "cuba_key", "uid"})
        attributes_string = str(attributes).lower() + "\n"
        with open(filename, 'w') as f:
            f.write("all_cuds_attributes = " + attributes_string)
            f.close()

    def _generate_init_file(self):
        """
        Generates the __init__ file in the cuds folder.
        """
        init_filename = os.path.join(self.output_folder, "__init__.py")
        with open(init_filename, 'w') as f:
            f.write("from cuba import CUBA \n")
            f.close()

    def _generate_enum_file(self):
        """
        Generates the enum with the entities from the ontology.
        """
        cuba_filename = os.path.join(self.output_folder, "cuba.py")
        enum = "from enum import Enum, unique\n\n"
        enum += "\n@unique\n"
        enum += "class CUBA(Enum):\n"
        for element in self._parser.get_entities():
            enum += "    " + element + " = \"" + element + "\"\n"

        with open(cuba_filename, 'w+') as f:
            f.write(enum)
            f.close()

    def _generate_template_instance(self):
        """
        Opens the template file and reads its content.
        """
        with open(self._template_filename, 'r') as f:
            template = f.read()
            f.close()
        self._template = Template(template)

    def _generate_class_file(self, original_class):
        """
        Creates a class file using the template.

        :param original_class: uppercase name of the entity
        """
        # Get the parent
        original_parent = self._parser.get_parent(original_class)
        if original_parent == "":
            original_parent = "..core.data_container"
            fixed_parent = "DataContainer"
        else:
            # Update the names to proper case
            fixed_parent = format_class_name(original_parent)

        parent_module = original_parent.lower()
        module = original_class.lower()

        fixed_class_name = format_class_name(original_class)

        # Wraps the text to 70 characters
        definition = fill(self._parser.get_definition(original_class))
        # Add indentation to the new lines
        definition = definition.replace("\n", "\n    ")

        arguments_init, attr_sent_super, attr_initialised = self.\
            _get_constructor_attributes(original_class)

        content = {
            'parent_module':            parent_module,
            'parent':                   fixed_parent,
            'class':                    fixed_class_name,
            'definition':               definition,
            'cuba_key':                 original_class,
            'arguments_init':           arguments_init,
            'attributes_sent_super':    attr_sent_super,
            'attributes_initialised':   attr_initialised
        }

        self._write_content_to_class_file(content, module)
        self._add_class_import_to_init(module, fixed_class_name)

    def _write_content_to_class_file(self, content, class_file):
        """
        Writes the content of the class to a python file.

        :param content: dictionary with the values for the template's keywords
        :param class_file: name of the class file
        """
        # Replace template tokens with specific values
        text = self._template.safe_substitute(content)

        # Create file from template substitutions
        filename = os.path.join(self.output_folder, class_file + ".py")
        with open(filename, 'w') as f:
            f.write(text)
            f.close()

    def _add_class_import_to_init(self, module_name, class_name):
        """
        Adds the import to the init file.

        :param module_name: name of the class file (module)
        :param class_name: name of the class
        """
        init_file = os.path.join(self.output_folder, "__init__.py")
        with open(init_file, 'a+') as f:
            f.write("from " + module_name + " import " + class_name + "\n")
            f.close()

    def _get_constructor_attributes(self, cuba_key):
        """
        Returns the attributes (own and inherited) used in the constructor.

        :param cuba_key: key of the entity
        :return: arguments_init: str all attributes
                 attr_sent_super: str inherited attributes
                 attr_initialised: str own, not inherited attributes
        """
        all_attr = self._parser.get_attributes(cuba_key)
        # Inherited attributes are sent to parent constructor
        inherited_attr = set(self._parser.get_inherited_attributes(cuba_key))
        # Own attributes are set in the constructor
        own_attr = set(self._parser.get_own_attributes(cuba_key))

        arguments_init = "self"
        attr_sent_super = ""
        attr_initialised = ""

        for a in all_attr:
            # Check that they are not instantiable classes
            if a.upper() in self.not_instantiable:
                arguments_init += ", " + a
                if a in inherited_attr:
                    attr_sent_super += a + ", "
                elif a in own_attr:
                    attr_initialised += "\n        self.{} = {}".format(a, a)
        if attr_initialised:
            attr_initialised += "\n"

        # Optional name property for all entities
        attr_sent_super += "name"

        return arguments_init, attr_sent_super, attr_initialised


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("YAML_file", help="Input YAML file")
    arg_parser.add_argument("template_file", help="Template class file")
    help_info = "Root folder for the generated files"
    arg_parser.add_argument("output_folder", help=help_info)
    args = arg_parser.parse_args()

    generator = ClassGenerator(args.YAML_file, args.template_file,
                               args.output_folder)
    generator.generate_classes()


if __name__ == "__main__":
    main()
