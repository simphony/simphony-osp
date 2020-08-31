"""Utilities used for the transport layer."""

import json
import uuid
import os
import shutil
import logging
import hashlib
from osp.core.namespaces import get_entity, cuba
from osp.core.utils import create_recycle
from osp.core.ontology.datatypes import convert_from, convert_to
from osp.core.ontology.entity import OntologyEntity
from osp.core.session.buffers import get_buffer_context_mngr

logger = logging.getLogger(__name__)

INITIALIZE_COMMAND = "_init"
LOAD_COMMAND = "_load"
HANDSHAKE_COMMAND = "_handshake"


def serialize_buffers(session_obj, buffer_context,
                      additional_items=None, target_directory=None):
    """Serialize the buffers and additional items.

    Args:
        session_obj (Session): Serialize the buffers of this session object.
        buffer_context (BufferContext): Which buffers to serialize
        additional_items (Dict[str, Any]): Additional items to be added
            to the serialized json object, defaults to None
        target_directory (Path): Where to move the files of the files cuds to
            serialize. If None, do not move them and return all the files
            corresponding to file cuds in the buffers.

    Returns:
        str, List[path]: The serialized buffers and the list of corresponding
            files.
    """
    result = dict()
    files = list()
    if buffer_context is not None:
        added, updated, deleted = session_obj._buffers[buffer_context]
        files += move_files(get_file_cuds(added.values()),
                            None, target_directory)
        files += move_files(get_file_cuds(updated.values()),
                            None, target_directory)
        result = {
            "added": serializable(added.values()),
            "updated": serializable(updated.values()),
            "deleted": serializable(deleted.values()),
        }

    result["expired"] = serializable(session_obj._expired)

    if additional_items is not None:
        for k, v in additional_items.items():
            files += move_files(get_file_cuds(v), None, target_directory)
            result[k] = serializable(v)
    if buffer_context is not None:
        session_obj._reset_buffers(buffer_context)
    return json.dumps(result), files


def deserialize_buffers(session_obj, buffer_context, data,
                        temp_directory=None, target_directory=None):
    """Deserialize serialized buffers.

    Add them to the session and push them
    to the registry of the given session object.
    Returns the deserialization of everything but the buffers.

    Args:
        session_obj (Session): The session object to load the buffers into.
        buffer_context (BufferContext): add the deserialized cuds objects to
            the selected buffers
        data (str): Serialized buffers
        temp_directory (Path): Where the files are stored of the to file cuds
            to deserialize are stored. If None, file cuds are assumed to have
            the full path.
        target_directory (Path): Where to move the files.
        If None, do not move them.

    Returns:
        Dict[str, Any]: Everything in data, that were not part of the buffers.
    """
    with get_buffer_context_mngr(session_obj, buffer_context):
        data = json.loads(data)

        if "expired" in data:
            session_obj.expire(
                *set(deserialize(json_obj=data["expired"],
                                 session=session_obj,
                                 buffer_context=buffer_context))
            )

        deserialized = dict()
        for k, v in data.items():
            d = deserialize(json_obj=v,
                            session=session_obj,
                            buffer_context=buffer_context,
                            _force=(k == "deleted"))
            deserialized[k] = d
            if k != "deleted":
                move_files(get_file_cuds(d), temp_directory, target_directory)
        deleted = deserialized["deleted"] if "deleted" in deserialized else []

        for x in deleted:
            session_obj._notify_delete(x)

        for cuds_object in deleted:
            if cuds_object.uid in session_obj._registry:
                del session_obj._registry[cuds_object.uid]
        return {k: v for k, v in deserialized.items()
                if k not in ["added", "updated", "deleted", "expired"]}


def move_files(file_cuds, temp_directory, target_directory):
    """Move the files associated with the given CUDS. Return all moved CUDS.

    Args:
        file_cuds (List[Cuds]): Cuds whose oclass is cuba.File
        temp_directory (path): The directory where the files are stored.
            If None, file cuds are expected to have the whole path.
        target_directory (path): The directory to move the files to.
            If None, do not move anything and return all file paths

    Returns:
        List[path]: The list of files moved (if target_directory not None) or
                    The list of all files (if target_directory None)
    """
    if target_directory is None:
        return [_convert_path_of_file_cuds(c) for c in file_cuds]
    result = list()
    for cuds in file_cuds:
        # get current location
        path = _convert_path_of_file_cuds(cuds)
        base_name = os.path.basename(path)
        if temp_directory is not None:
            path = os.path.join(temp_directory,
                                base_name)
        # get target location
        if not base_name.startswith(cuds.uid.hex):
            base_name = cuds.uid.hex + "-" + base_name
        target_path = os.path.join(target_directory, base_name)
        # copy
        if (
            os.path.exists(os.path.dirname(target_path))
            and os.path.exists(path)
            and not (
                os.path.exists(target_path)
                and os.path.samefile(path, target_path)
            )
        ):
            shutil.copyfile(path, target_path)
            assert cuds.uid not in cuds.session._expired
            cuds.path = target_path
            logger.debug(
                "Copy file %s to %s" % (repr(path), repr(target_path))
            )
            result.append(target_path)
        else:
            logger.debug(
                "Will not move %s to %s" % (repr(path), repr(target_path))
            )
            if not os.path.exists(os.path.dirname(target_path)):
                logger.debug("Reason: Target path does not exist")
            elif not os.path.exists(path):
                logger.debug("Reason: File to move does not exist")
            elif os.path.exists(target_path) and os.path.samefile(
                path,
                target_path
            ):
                logger.debug("Reason: The exact same file is already present "
                             "at the destination")
    return result


def deserialize(json_obj, session, buffer_context, _force=False):
    """Deserialize a json object, instantiate the Cuds object in there.

    Args:
        json_obj (Union[Dict, List, str, None]): The json object to
            deserialize.
        session (Session): When creating a cuds_object, use this session.
        buffer_context (BufferContext): add the deserialized cuds objects to
            the selected buffers.

    Raises:
        ValueError: The json object could not be deserialized.

    Returns:
        Union[Cuds, UUID, List[Cuds], List[UUID], None]: The deserialized
            object.
    """
    if json_obj is None:
        return None
    if isinstance(json_obj, (str, int, float)):
        return json_obj
    if isinstance(json_obj, list):
        return [deserialize(x, session, buffer_context, _force=_force)
                for x in json_obj]
    if isinstance(json_obj, dict) \
            and "oclass" in json_obj \
            and "uid" in json_obj \
            and "attributes" in json_obj \
            and "relationships" in json_obj:
        cuds = _to_cuds_object(json_obj, session, buffer_context,
                               _force=_force)
        return cuds
    if isinstance(json_obj, dict) \
            and set(["UUID"]) == set(json_obj.keys()):
        return convert_to(json_obj["UUID"], "UUID")
    if isinstance(json_obj, dict) \
            and set(["ENTITY"]) == set(json_obj.keys()):
        return get_entity(json_obj["ENTITY"])
    if isinstance(json_obj, dict):
        return {k: deserialize(v, session, buffer_context, _force=_force)
                for k, v in json_obj.items()}
    raise ValueError("Could not deserialize %s." % json_obj)


def serializable(obj):
    """Make given object json serializable.

    The object can be a cuds_object, a list of cuds_objects,
    a uid or a list od uids.

    Args:
        obj (Union[Cuds, UUID, List[Cuds], List[UUID], None]): The object to
            make serializable.

    Raises:
        ValueError: Given object could not be made serializable.

    Return:
        Union[Dict, List, str, None]: The serializable object.
    """
    from osp.core.cuds import Cuds
    if obj is None:
        return obj
    if isinstance(obj, (str, int, float)):
        return obj
    if isinstance(obj, uuid.UUID):
        return {"UUID": convert_from(obj, "UUID")}
    if isinstance(obj, OntologyEntity):
        return {"ENTITY": str(obj)}
    if isinstance(obj, Cuds):
        return _serializable(obj)
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    try:
        return [serializable(x) for x in obj]
    except TypeError as e:
        raise ValueError("Could not serialize %s." % obj) \
            from e


def get_file_cuds(obj):
    """Get the file cuds out of cuds_object, or list of cuds_objects.

    Args:
        obj (Union[Cuds, UUID, List[Cuds], List[UUID], None]): The object to
            check for fie cuds..

    Returns:
        List[Cuds]: The list of file cuds
    """
    from osp.core.cuds import Cuds

    if isinstance(obj, Cuds) and obj.is_a(cuba.File):
        return [obj]
    if isinstance(obj, (Cuds, str, float, int, uuid.UUID, OntologyEntity)) \
            or obj is None:
        return []
    if isinstance(obj, dict):
        obj = obj.values()
    return [y for x in obj for y in get_file_cuds(x)]


def _serializable(cuds_object):
    """Make a cuds_object json serializable.

    Returns:
        Cuds: The cuds_object to make serializable.
    """
    result = {"oclass": str(cuds_object.oclass),
              "uid": convert_from(cuds_object.uid, "UUID"),
              "attributes": dict(),
              "relationships": dict()}
    for attribute, value in cuds_object.get_attributes().items():
        result["attributes"][attribute.argname] = convert_from(
            value, attribute.datatype
        )
    for rel in cuds_object._neighbors:
        result["relationships"][str(rel)] = {
            convert_from(uid, "UUID"): str(oclass)
            for uid, oclass in cuds_object._neighbors[rel].items()
        }
    return result


def _to_cuds_object(json_obj, session, buffer_context, _force=False):
    """Transform a json serializable dict to a cuds_object.

    Args:
        json_obj (Dict[str, Any]): The json object to convert to a Cuds object.
        session (Session): The session to add the cuds object to.
        buffer_context (BufferContext): add the deserialized cuds objects to
            the selected buffers.

    Returns:
        Cuds: The resulting cuds_object.
    """
    if buffer_context is None:
        raise ValueError("Not allowed to deserialize CUDS object "
                         "with undefined buffer_context")
    with get_buffer_context_mngr(session, buffer_context):
        oclass = get_entity(json_obj["oclass"])
        attributes = json_obj["attributes"]
        relationships = json_obj["relationships"]
        cuds_object = create_recycle(oclass=oclass,
                                     kwargs=attributes,
                                     session=session,
                                     uid=json_obj["uid"],
                                     fix_neighbors=False,
                                     _force=_force)

        for rel_name, obj_dict in relationships.items():
            rel = get_entity(rel_name)
            cuds_object._neighbors[rel] = {}
            for uid, target_name in obj_dict.items():
                uid = convert_to(uid, "UUID")
                target_oclass = get_entity(target_name)
                cuds_object._neighbors[rel][uid] = target_oclass
        return cuds_object


def get_hash_dir(directory_path):
    """Get the has sums of all files in the given path.

    Args:
        directory_path (path): The path to the directory

    Returns:
        Dict[path, HASH]: The sha256 HASH object for each file in the directory
    """
    result = dict()
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        if not os.path.isfile(file_path):
            continue
        result[file] = get_hash(file_path)
    return result


def check_hash(file_path, file_hashes):
    """Check whether the hash of the given file is in the given dictionary.

    If not, add it.

    Args:
        file_path (path): The path to the file to check
        file_hashes (Dict[str, HASH]): Dictionary from file basename to hash
    """
    sha265hash = get_hash(file_path)
    filename = os.path.basename(file_path)
    if filename in file_hashes:
        if file_hashes[filename] == sha265hash:
            return True
        else:
            logger.debug(
                "Hash mismatch for file %s. File on disk has hash %s,"
                " and last registered version has hash %s."
                % (filename, sha265hash, file_hashes[filename]))
    file_hashes[filename] = sha265hash
    return False


def get_hash(file_path):
    """Get the hash of the given file.

    Args:
        file_path (path): A path to a file

    Returns:
        HASH: A sha256 HASH object
    """
    buf_size = 4096
    result = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            result.update(data)
    return result.hexdigest()


def _convert_path_of_file_cuds(file_cuds):
    if os.name not in ['nt', 'posix']:
        raise Exception('Your machine is not supported.')

    path_type = _determine_path_type_of_file_cuds(file_cuds)
    path = file_cuds.path

    if path_type == 'windows':
        # on windows machine
        if os.name == 'nt':
            return path
        # on linux machine
        else:
            return path.replace('\\', '/')
    # linux path
    elif path_type == 'linux':
        # on linux machine
        if os.name == 'posix':
            return path
        # on windows machine
        else:
            return path.replace('/', '\\')


def _determine_path_type_of_file_cuds(file_cuds):
    path = file_cuds.path
    if '\\' in path and '/' not in path:    # windows path
        return 'windows'
    elif '/' in path and '\\' not in path:    # linux path
        return 'linux'
    # doesn't matter (path is just a file name)
    elif '/' not in path and '\\' not in path:
        return 'linux'
    else:
        raise Exception("""Inconsistent path attribute for
        CUBA.FILE object {} with
        path {}.""".format(file_cuds.uid, path))
