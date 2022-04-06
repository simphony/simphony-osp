"""Utilities used in the communication in the transport layer."""

import hashlib
import logging
import math
import os

from osp.core.session.transport.transport_utils import check_hash

logger = logging.getLogger(__name__)
BLOCK_SIZE = 4096
LEN_FILES_HEADER = [5]  # num_blocks


def decode_header(bytestring, lengths):
    """Decode the header given as a string of bytes.

    Args:
        bytestring (bytes): The encoded header
        lengths (List[int]): The number of bytes for the individual components

    Yields:
        Union[int, str]: Interpret all elements that have a corresponding
                         length as int. If there leftover bytes decode them
                         using utf-8.
    """
    i = 0
    for length in lengths:
        if i + length > len(bytestring):
            raise IndexError("Length mismatch in header")
        yield int.from_bytes(bytestring[i : i + length], byteorder="big")
        i += length
    if len(bytestring) > i:
        yield bytestring[i:].decode("utf-8")


def encode_header(elements, lengths):
    """Encode the header to single array of bytes.

    Args:
        elements (Union[int, str]): The elements to encode. All but the last
                                    must be int. The last one can be str.
        lengths ([type]): The number of bytes in the encoded header.

    Raises:
        ValueError: elements and lengths mismatch in number of elements
        NotImplementedError: Invalid datatype in elements.

    Returns:
        bytes: The encoded header
    """
    r = b""
    if len(lengths) > len(elements) or len(elements) > len(lengths) + 1:
        raise ValueError
    for element, length in zip(elements, lengths):
        if not isinstance(element, int):
            raise NotImplementedError
        r += element.to_bytes(length=length, byteorder="big")
    if len(elements) > len(lengths):
        if not isinstance(elements[-1], str):
            raise NotImplementedError("Invalid type of %s" % elements[-1])
        r += elements[-1].encode("utf-8")
    return r


def split_message(msg, block_size=BLOCK_SIZE):
    """Split the message to send in small blocks.

    Args:
        msg (str): The message to send.
        block_size (int, optional): The size of the blocks.
                                    Defaults to BLOCK_SIZE.

    Returns:
        int, Generator: Number of blocks, Generator over blocks.
    """
    msg = msg.encode("utf-8")
    num_blocks = int(math.ceil(len(msg) / block_size))

    def gen(msg, num_blocks, block_size):
        for i in range(num_blocks):
            logger.debug(
                "Sending message block %s of %s" % (i + 1, num_blocks)
            )
            yield msg[i * block_size : (i + 1) * block_size]
        logger.debug("Done")

    return num_blocks, gen(msg, num_blocks, block_size)


async def join_message(websocket, num_blocks):
    """Get the message that was decomposed in different blocks.

    Args:
        websocket (websocket): wecksocket object to receive the objects.
        num_blocks (int): The number of blocks that belong to the message.

    Returns:
        str: The data, decoded using utf-8.
    """
    data = b""
    for i in range(num_blocks):
        logger.debug("Receiving message block %s of %s" % (i + 1, num_blocks))
        data += await websocket.recv()
    logger.debug("Done")
    data = data.decode("utf-8")
    return data


def filter_files(files, file_hashes):
    """Remove the files the receiver already has.

    Args:
        files (List[path]): A list of paths to send.

    Yields:
        List[str]: The files to send
    """
    result = list()
    for file in files:
        if not os.path.exists(file):
            logger.warning("Cannot send %s, because it does not exist" % file)
            continue
        if check_hash(file, file_hashes):
            logger.debug(
                "Skip sending file %s, "
                "receiver already has a copy of it." % file
            )
            continue
        result.append(file)
    return result


def encode_files(files):
    """Encode the files to be sent to over the networks.

    Will send file in several blocks.

    Args:
        files (List[path]): A list of paths to send.

    Yields:
        bytes: The bytes of the file
    """
    logger.debug("Will send %s files" % len(files))
    for i, file in enumerate(files):
        filename = os.path.basename(file)
        num_blocks = int(math.ceil(os.path.getsize(file) / BLOCK_SIZE))
        logger.debug(
            "Send file %s (%s of %s) with %s block(s) of %s bytes"
            % (file, i + 1, len(files), num_blocks, BLOCK_SIZE)
        )
        yield encode_header([num_blocks, filename], LEN_FILES_HEADER)

        # send the file contents
        with open(file, "rb") as f:
            for i, block in enumerate(iter(lambda: f.read(BLOCK_SIZE), b"")):
                logger.debug("Send file block %s of %s" % (i + 1, num_blocks))
                yield block
            logger.debug("Done")


async def receive_files(num_files, websocket, directory, file_hashes=None):
    """Will receive and store the files sent to the websocket.

    Args:
        num_files (int): The number of files to load.
        websocket (websocket): The websocket to load the files from.
        directory (path): The location to store the files.
        file_hashes(dict[str, str]): Hashes of files of already received files.
    """
    if file_hashes is None:
        file_hashes = dict()
    for i in range(num_files):
        logger.debug("Load file %s of %s" % (i + 1, num_files))
        num_blocks, filename = decode_header(
            await websocket.recv(), LEN_FILES_HEADER
        )
        filename = os.path.basename(filename)
        file_hashes[filename] = hashlib.sha256()
        file_path = os.path.join(directory, filename)
        logger.debug(
            "Storing file %s with %s blocks." % (file_path, num_blocks)
        )
        with open(file_path, "wb") as f:
            for j in range(num_blocks):
                logger.debug("Receive block %s of %s" % (j + 1, num_blocks))
                data = await websocket.recv()
                file_hashes[filename].update(data)
                f.write(data)
            logger.debug("Done")
        file_hashes[filename] = file_hashes[filename].hexdigest()
