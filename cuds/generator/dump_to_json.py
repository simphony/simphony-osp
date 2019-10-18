import cuds.utils as utils

# The resulting JSON file represents the internal structure of the CUDS.

attribute_key = "attributes"


def dump_cuds(cuds_object, prefix=""):
    """
    Iteratively writes cuds object to JSON file.

    :param cuds_object: cuds object to be written to JSON file
    :param prefix: string with json prefix
    :return: string in json format
    """
    json = prefix + "{\n"
    json += dump_attributes(cuds_object, prefix + "  ")
    for key, val in cuds_object.iteritems():
        json += ",\n"
        json += prefix + " \"" + str(key) + "\": \n"
        json += dump_cuds_same_key(val, prefix + "    ")
    json += "\n" + prefix + "}"
    return json


def dump_attributes(cuds_object, prefix=""):
    """
    Writes the attributes of the given element to the file.

    :param cuds_object: current cuds element
    :param prefix: string with json prefix
    :return: string in json format
    """
    json = prefix + "\"" + attribute_key + "\": \n"
    json += prefix + "    {\n"
    attributes = utils.filter_cuds_attr(cuds_object)
    for a in attributes:
        json += prefix + "     \"" + a + "\": \""
        json += str(getattr(cuds_object, a)) + "\",\n"
    json = json[:-2] + "\n"
    json += prefix + "    }"
    return json


def dump_cuds_same_key(cuds_same_key, prefix=""):
    """
    Writes the cuds objects with the same key to the json file
    using the dump_cuds() function.

    :param cuds_same_key: the cuds objects with the same key
    :param prefix: string with json prefix
    :return: string in json format
    """
    json = prefix + "{\n"
    for key, cuds_object in cuds_same_key.iteritems():
        json += prefix + " \"" + str(key) + "\": \n"
        json += dump_cuds(cuds_object, prefix + "    ") + ",\n"
    json = json[:-2] + "\n"
    json += prefix + "}"
    return json
