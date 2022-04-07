"""Utilities used for the transport layer."""

import ast
import filecmp
import hashlib
import json
import logging
import os
import shutil
import uuid
from typing import Any, Optional, Tuple

import rdflib
from rdflib import __version__ as rdflib_version

if rdflib_version >= "6":
    from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf
    from rdflib.plugins.serializers.jsonld import from_rdf as json_from_rdf
else:
    import warnings

    def _silent_warn(*args, **kwargs) -> None:
        """Function to replace `warnings.warn`, silences forced warnings."""
        pass

    warn = warnings.warn
    warnings.warn = _silent_warn
    from rdflib_jsonld.parser import to_rdf as json_to_rdf
    from rdflib_jsonld.serializer import from_rdf as json_from_rdf

    warnings.warn = warn
from osp.core.namespaces import cuba, get_entity
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.datatypes import convert_from, convert_to
from osp.core.ontology.entity import OntologyEntity
from osp.core.session.buffers import BufferContext, get_buffer_context_mngr
from osp.core.utils.general import uid_from_iri
from osp.core.utils.wrapper_development import create_from_triples

logger = logging.getLogger(__name__)

INITIALIZE_COMMAND = "_init"
LOAD_COMMAND = "_load"
HANDSHAKE_COMMAND = "_handshake"

serialization_initialized = False


def serialize_buffers(
    session_obj,
    buffer_context,
    additional_items=None,
    target_directory=None,
    file_cuds_uid=True,
):
    """Serialize the buffers and additional items.

    Args:
        session_obj (Session): Serialize the buffers of this session object.
        buffer_context (BufferContext): Which buffers to serialize
        additional_items (Dict[str, Any]): Additional items to be added
            to the serialized json object, defaults to None
        target_directory (Path): Where to move the files of the files cuds to
            serialize. If None, do not move them and return all the files
            corresponding to file cuds in the buffers.
        file_cuds_uid (bool): Whether to prepend the CUDS uid to the file name
            on the target location.

    Returns:
        str, List[path]: The serialized buffers and the list of corresponding
            files.
    """
    result = dict()
    files = list()
    if buffer_context is not None:
        added, updated, deleted = session_obj._buffers[buffer_context]
        files += move_files(
            get_file_cuds(added.values()),
            None,
            target_directory,
            file_cuds_uid=file_cuds_uid,
        )
        files += move_files(
            get_file_cuds(updated.values()),
            None,
            target_directory,
            file_cuds_uid=file_cuds_uid,
        )
        result = {
            "added": serializable(added.values()),
            "updated": serializable(updated.values()),
            "deleted": serializable(deleted.values()),
        }

    result["expired"] = serializable(session_obj._expired)

    if additional_items is not None:
        for k, v in additional_items.items():
            files += move_files(
                get_file_cuds(v),
                None,
                target_directory,
                file_cuds_uid=file_cuds_uid,
            )
            result[k] = serializable(v)
    if buffer_context is not None:
        session_obj._reset_buffers(buffer_context)
    return json.dumps(result), files


def deserialize_buffers(
    session_obj,
    buffer_context,
    data,
    temp_directory=None,
    target_directory=None,
    file_cuds_uid=True,
):
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
        file_cuds_uid (bool): Whether to prepend the CUDS uid to the file name
            on the target location.

    Returns:
        Dict[str, Any]: Everything in data, that were not part of the buffers.
    """
    with get_buffer_context_mngr(session_obj, buffer_context):
        data = json.loads(data)

        if "expired" in data:
            session_obj.expire(
                *set(
                    deserialize(
                        json_obj=data["expired"],
                        session=session_obj,
                        buffer_context=buffer_context,
                    )
                )
            )

        deserialized = dict()
        for k, v in data.items():
            d = deserialize(
                json_obj=v,
                session=session_obj,
                buffer_context=buffer_context,
                _force=(k == "deleted"),
            )
            deserialized[k] = d
            if k != "deleted":
                move_files(
                    get_file_cuds(d),
                    temp_directory,
                    target_directory,
                    file_cuds_uid=file_cuds_uid,
                )
        deleted = deserialized["deleted"] if "deleted" in deserialized else []

        for x in deleted:
            session_obj._notify_delete(x)

        for cuds_object in deleted:
            if cuds_object.uid in session_obj._registry:
                del session_obj._registry[cuds_object.uid]
        return {
            k: v
            for k, v in deserialized.items()
            if k not in ["added", "updated", "deleted", "expired"]
        }


def move_files(
    file_cuds, temp_directory, target_directory, file_cuds_uid=True
):
    """Move the files associated with the given CUDS. Return all moved CUDS.

    Args:
        file_cuds (List[Cuds]): Cuds whose oclass is cuba.File
        temp_directory (path): The directory where the files are stored.
            If None, file cuds are expected to have the whole path.
        target_directory (path): The directory to move the files to.
            If None, do not move anything and return all file paths
        file_cuds_uid (bool): Whether to prepend the CUDS uid to the file name
            on the target location.

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
            path = os.path.join(temp_directory, base_name)
        # get target location
        # fix prefix (add in server, remove in client)
        if file_cuds_uid and not base_name.startswith(cuds.uid.hex):
            base_name = cuds.uid.hex + "-" + base_name
        elif not file_cuds_uid and base_name.startswith(
            str(cuds.uid.hex) + "-"
        ):
            base_name = base_name[len(str(cuds.uid.hex) + "-") :]
        # fix suffix (remove in server)
        if file_cuds_uid:
            name, ext = os.path.splitext(base_name)
            if name.endswith(f" ({cuds.uid})"):
                name = name[0 : name.find(f" ({cuds.uid})")]
                base_name = f"{name}{ext}"
        target_path = os.path.join(target_directory, base_name)
        # copy
        if (
            os.path.exists(os.path.dirname(target_path))
            and os.path.exists(path)
        ) and (
            not os.path.exists(target_path)
            or not os.path.samefile(path, target_path)
        ):
            # Append CUDS uid.
            if (
                not file_cuds_uid
                and os.path.exists(target_path)
                and not filecmp.cmp(path, target_path)
            ):
                name, ext = os.path.splitext(os.path.basename(target_path))
                name += f" ({cuds.uid})"
                target_path = os.path.join(
                    os.path.dirname(target_path), name + ext
                )
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
            cuds.path = ""
            if not os.path.exists(os.path.dirname(target_path)):
                logger.debug("Reason: Target path does not exist")
            elif os.path.exists(target_path) and (
                os.path.exists(path)
                and os.path.samefile(path, target_path)
                or not os.path.exists(path)
            ):
                # The above expression has the form A ( BC + ~B ) = ABC + A~B.
                # The meaning of the first minterm is clear, but the meaning
                # of the second is not. The reason why it is there is
                # because when the hash of the file that should be loaded
                # coincides with the hash of one of the files in the target
                # directory, the server does not send the file. However,
                # the cuds path should still be updated.
                logger.debug(
                    "Reason: The exact same file is already present "
                    "at the destination"
                )
                cuds.path = target_path
            elif not os.path.exists(path):
                logger.debug("Reason: File to move does not exist")
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
    if (
        isinstance(json_obj, list)
        and json_obj
        and isinstance(json_obj[0], dict)
        and "@id" in json_obj[0]
    ):
        return _to_cuds_object(
            json_obj, session, buffer_context, _force=_force
        )
    if isinstance(json_obj, list):
        return [
            deserialize(x, session, buffer_context, _force=_force)
            for x in json_obj
        ]
    if isinstance(json_obj, dict) and set(["UID"]) == set(json_obj.keys()):
        return convert_to(json_obj["UID"], "UID")
    if isinstance(json_obj, dict) and set(["ENTITY"]) == set(json_obj.keys()):
        return get_entity(json_obj["ENTITY"])
    if isinstance(json_obj, dict):
        return {
            k: deserialize(v, session, buffer_context, _force=_force)
            for k, v in json_obj.items()
        }
    raise ValueError("Could not deserialize %s." % json_obj)


def serializable(obj, partition_cuds=True, mark_first=False):
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
        return {"UID": convert_from(obj, "UID")}
    if isinstance(obj, OntologyEntity):
        return {"ENTITY": str(obj)}
    if isinstance(obj, Cuds):
        return _serializable([obj])
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    if not partition_cuds:  # TODO this should be the default
        try:
            return _serializable(obj, mark_first=mark_first)
        except TypeError:
            pass
    try:
        return [serializable(x) for x in obj]
    except TypeError as e:
        raise ValueError("Could not serialize %s." % obj) from e


def get_file_cuds(obj):
    """Get the file cuds out of cuds_object, or list of cuds_objects.

    Args:
        obj (Union[Cuds, UUID, URIRef, List[Cuds], List[Union[UUID, URIRef],
             None]): The object to check for file cuds.

    Returns:
        List[Cuds]: The list of file cuds
    """
    from osp.core.cuds import Cuds

    if isinstance(obj, Cuds) and obj.is_a(cuba.File):
        return [obj]
    if (
        isinstance(obj, (Cuds, str, float, int, uuid.UUID, OntologyEntity))
        or obj is None
    ):
        return []
    if isinstance(obj, dict):
        obj = obj.values()
    return [y for x in obj for y in get_file_cuds(x)]


def _serializable(cuds_objects, mark_first=False):
    """Make CUDS objects json serializable using JSON-LD.

    Args:
        cuds_objects ([type]): The CUDS objects to make serializable.

    Returns:
        List[Dict]: []
    """
    from osp.core.cuds import Cuds
    from osp.core.ontology.namespace_registry import namespace_registry

    g = rdflib.Graph()
    g.namespace_manager = namespace_registry._graph.namespace_manager
    g.bind("cuds", rdflib.URIRef("http://www.osp-core.com/cuds#"))
    if mark_first:
        g.add(
            (
                rdflib_cuba._serialization,
                rdflib.RDF.first,
                rdflib.Literal(str(next(iter(cuds_objects)).uid)),
            )
        )
    for cuds_object in cuds_objects:
        if not isinstance(cuds_object, Cuds):
            raise TypeError(
                f"Called _serializable with non-CUDS object "
                f"{cuds_object} of type {type(cuds_object)}"
            )
        for s, p, o in cuds_object.get_triples(include_neighbor_types=True):
            if isinstance(o, rdflib.Literal):
                o = rdflib.Literal(
                    convert_from(o.toPython(), o.datatype),
                    datatype=o.datatype,
                    lang=o.language,
                )
            g.add((s, p, o))
    return json_from_rdf(g, auto_compact=len(cuds_objects) > 1)


def _to_cuds_object(json_obj, session, buffer_context, _force=False):
    """Transform a json serializable dict to a cuds_object.

    Args:
        json_obj (Dict[str, Any]): The json object to convert to a Cuds object.
        session (Session): The session to add the cuds object to.
        buffer_context (BufferContext): add the deserialized cuds object to
            the selected buffers.

    Returns:
        Cuds: The resulting cuds_object.
    """
    if not isinstance(buffer_context, BufferContext):
        raise ValueError(
            "Not allowed to deserialize CUDS object "
            "with undefined buffer_context"
        )
    with get_buffer_context_mngr(session, buffer_context):
        g = json_to_rdf(json_obj, rdflib.Graph())
        try:
            this_s = next(s for s, p, _ in g if p != rdflib.RDF.type)
        except StopIteration:
            this_s = next(s for s, p, _ in g)

        triples, neighbor_triples = set(), set()
        for s, p, o in g:
            if s == this_s:
                # datatype conversion
                if (
                    isinstance(o, rdflib.Literal)
                    and o.datatype
                    and o.datatype in rdflib_cuba
                    and "VECTOR" in o.datatype.toPython()
                ):
                    o = rdflib.Literal(
                        convert_to(ast.literal_eval(o.toPython()), o.datatype),
                        datatype=o.datatype,
                        lang=o.language,
                    )
                triples.add((s, p, o))
            else:
                neighbor_triples.add((s, p, o))

        cuds = create_from_triples(
            triples, neighbor_triples, session, fix_neighbors=False
        )
        return cuds


def import_rdf(graph, session, buffer_context, return_uid=None):
    """Import RDF Graph to CUDS.

    Args:
        graph (rdflib.Graph): The graph to import.
        session (Session): The session to add the CUDS objects to.
        buffer_context (BufferContext): add the deserialized cuds objects to
            the selected buffers.
        return_uid (Union[UUID, URIRef]): Return only the object with
        the given uid.

    Raises:
        ValueError: Not allowed to deserialize with undefined buffer context.

    Returns:
        List[Cuds]: The deserialized CUDS objects.
    """
    if not isinstance(buffer_context, BufferContext):
        raise ValueError(
            "Not allowed to deserialize CUDS object "
            "with undefined buffer_context"
        )

    get_buffer_context_mngr(session, buffer_context)
    triples = (triple for triple in graph if _import_rdf_filter(triple))
    triples = map(_import_rdf_custom_datatypes, triples)
    uid_triples = dict()
    for s, p, o in triples:
        s_uid = uid_from_iri(s)
        session.graph.add((s, p, o))
        uid_triples[s_uid] = uid_triples.get(s_uid, set())
        uid_triples[s_uid].add((s, p, o))
    result = list()
    for uid, t in uid_triples.items():
        # Create entry in the registry
        x = create_from_triples(t, set(), session, fix_neighbors=False)
        if return_uid is None or uid == return_uid:
            result.append(x)
    return result if not return_uid else result[0]


def _import_rdf_filter(
    triple: Tuple[Any, Any, Any]
) -> Optional[Tuple[Any, Any, Any]]:
    """Auxiliary function for `import_rdf`.

    Filters triples blank nodes and named individuals.
    """
    s, p, o = triple
    if (
        isinstance(s, rdflib.BNode)
        or isinstance(o, rdflib.BNode)
        or o == rdflib.OWL.NamedIndividual
    ):
        return None
    else:
        return triple


def _import_rdf_custom_datatypes(
    triple: Tuple[Any, Any, Any]
) -> Tuple[Any, Any, Any]:
    """Auxiliary function for `import_rdf`.

    Handles custom datatypes in a triple (if any).
    """
    s, p, o = triple
    # handle custom datatype: VECTORs
    if (
        isinstance(o, rdflib.Literal)
        and o.datatype
        and o.datatype in rdflib_cuba
        and "VECTOR" in o.datatype.toPython()
    ):
        o = rdflib.Literal(
            convert_to(ast.literal_eval(o.toPython()), o.datatype),
            datatype=o.datatype,
            lang=o.language,
        )
    return s, p, o


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
                % (filename, sha265hash, file_hashes[filename])
            )
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
    if os.name not in ["nt", "posix"]:
        raise Exception("Your machine is not supported.")

    path_type = _determine_path_type_of_file_cuds(file_cuds)
    path = file_cuds.path

    if path_type == "windows":
        # on windows machine
        if os.name == "nt":
            return path
        # on linux machine
        else:
            return path.replace("\\", "/")
    # linux path
    elif path_type == "linux":
        # on linux machine
        if os.name == "posix":
            return path
        # on windows machine
        else:
            return path.replace("/", "\\")


def _determine_path_type_of_file_cuds(file_cuds):
    path = file_cuds.path
    if "\\" in path and "/" not in path:  # windows path
        return "windows"
    elif "/" in path and "\\" not in path:  # linux path
        return "linux"
    # doesn't matter (path is just a file name)
    elif "/" not in path and "\\" not in path:
        return "linux"
    else:
        raise Exception(
            """Inconsistent path attribute for
        CUBA.FILE object {} with
        path {}.""".format(
                file_cuds.uid, path
            )
        )
