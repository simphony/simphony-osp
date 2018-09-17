
attribute_key = "attributes"


def dump_cuds(cuds_object, prefix=""):
    json = prefix + "{\n"
    json += dump_attributes(cuds_object, prefix + "  ")
    for key, val in cuds_object.iteritems():
        json += ",\n"
        json += prefix + " \"" + str(key) + "\": \n"
        json += dump_cuds_same_key(val, prefix + "    ")
    json += "\n" + prefix + "}"
    return json


def dump_attributes(cuds_object, prefix=""):
    json = prefix + "\"" + attribute_key + "\": \n"
    json += prefix + "    {\n"
    attributes = _filter_attr(cuds_object)
    for a in attributes:
        json += prefix + "     \"" + a + "\": \"" + str(getattr(cuds_object, a)) + "\",\n"
    json = json[:-2] + "\n"
    json += prefix + "    }"
    return json


def dump_cuds_same_key(cuds_same_key, prefix=""):
    json = prefix + "{\n"
    for key, cuds_object in cuds_same_key.iteritems():
        json += prefix + " \"" + str(key) + "\": \n"
        json += dump_cuds(cuds_object, prefix + "    ") + ",\n"
    json = json[:-2] + "\n"
    json += prefix + "}"
    return json


def _filter_attr(item):
    """
    Filters the non-relevant attributes from an object.

    :return: set with the filtered, relevant attributes
    """
    # Filter the magic functions
    attributes = [a for a in dir(item) if not a.startswith("__")]
    # Filter the added methods
    attributes = [a for a in attributes if not callable(getattr(item, a))]
    # Filter the explicitly unwanted attributes
    attributes = [a for a in attributes if a not in {'restricted_keys'}]

    return attributes
