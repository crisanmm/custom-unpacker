"""
Provides the main functionality of Cup.

Provides implementation for the following functions:
pack -- Pack files into an archive.
unpack -- Unpack files from an archive.
info -- Get information about the files in an archive.
"""

from pathlib import Path
from os import PathLike
from typing import *
from typing import BinaryIO
import logging

from .fileheader import FileHeader
from .exceptions import *

CHUNK_SIZE = 4096
FILE_SIGNATURE = b'__C__U__P__'


# logging.basicConfig(filename="cup.log", level=logging.DEBUG, format="%(asctime)s:%(levelname)s:%(message)s")


def pack(*paths: Union[str, bytes, PathLike],
         archive_name: Union[str, bytes, PathLike] = "archive.cup") -> None:
    """Pack files/directories into an archive.

    The files/directories specified in the `paths` variable length argument are
    packed into an archive with the name specified by the `archive_name` keyword argument.
    Only the basename of the specified files in `paths` will be kept. If a path to a directory is passed
    then the basename of it will be kept and all the other files inside it will have the path relative to
    the directory.

    :param paths: Variable length argument that specifies a list of files or directories to be added to the archive.
    :param archive_name: Name of the archive where all files will be added.
    """
    file_header_list, file_path_list = _header_path_list_from_paths(*paths)
    if Path(os.path.abspath(archive_name)) in file_path_list:
        raise ArchiveAlreadyExistsError(archive_name)

    logging.info(f"packing {paths} to {archive_name}...")
    with open(archive_name, 'wb') as archive:
        # Write file signature
        archive.write(FILE_SIGNATURE)

        for file_header in file_header_list:
            archive.write(file_header.header_array)
        for path in file_path_list:
            with open(path, 'rb') as file:
                while chunk := file.read(CHUNK_SIZE):
                    archive.write(chunk)
    logging.info(f"packed {paths} to {archive_name}")


def info(archive_path: Union[str, bytes, PathLike]) -> List[Tuple[int, int, int, str]]:
    """Get information about an archive.

    Gets all the information about the files in this archive using the file headers from the archive file
    specified in the `archive_path` argument.

    :param archive_path: Path of the archive.
    :return: 4-tuple containing information about the file, of the form
     (index in archive, size, timestamp of last modification, path).
    """
    file_header_list = _header_list_from_archive(archive_path)

    file_info_list = []
    for index, fh in enumerate(file_header_list):
        file_info_list.append((index, fh.file_size, fh.file_timestamp, fh.file_path))
    logging.info(f"gathered info for {archive_path}")
    return file_info_list


def unpack(*renaming: Tuple[Union[int, str], str],
           archive_path: Union[str, bytes, PathLike],
           destination_path: Union[str, bytes, PathLike]) -> None:
    """Unpack the archive.

    Unpacks the archive specified by the `archive_path` argument into the destination path specified
    by the `destination_path` argument. The `renaming` variable length argument consists of tuples of the form
    (old file name in archive, new file name).

    :param renaming: Optional variable length argument specifying renaming of files.
    :param archive_path: Path of the archive to unpack.
    :param destination_path: Path where the archive will be unpacked.
    """
    archive_path = Path(archive_path).resolve()
    file_header_list = _header_list_from_archive(archive_path)
    previous_working_directory = os.getcwd()

    _create_destination_path(destination_path)

    if renaming:
        renaming = {original_name: changed_name for original_name, changed_name in renaming}
        file_header_list = filter(lambda fh: fh.file_path in renaming.keys(), file_header_list)
        file_header_list = list(map(lambda fh: fh.with_different_path(renaming[fh.file_path]), file_header_list))

    os.chdir(destination_path)
    logging.info(f"unpacking {archive_path} to {destination_path}...")
    with open(archive_path, 'rb') as archive:
        for file_header in file_header_list:
            _create_file_path(file_header.file_path)
            _unpack_file(file_header, archive)
    os.chdir(previous_working_directory)
    logging.info(f"unpacked {archive_path} to {destination_path}")


def _header_list_from_archive(archive_path: Union[str, bytes, PathLike]) -> List[FileHeader]:
    """Internal function.

    Used for unpacking archives and getting information about the files in the archives.

    :param archive_path: Path to the archive.
    :return: List of file headers.
    """
    if not Path(archive_path).exists():
        raise ArchiveNonExistentError(archive_path)

    file_header_list = []
    with open(archive_path, 'rb') as archive:
        # Check for file signature
        if archive.read(len(FILE_SIGNATURE)) != FILE_SIGNATURE:
            raise ArchiveNotRecognizableError(archive_path)

        file_header = FileHeader.from_archive(archive)
        file_header_list.append(file_header)
        header_list_sentinel = file_header.file_offset

        current_seek = archive.seek(file_header.header_size, os.SEEK_CUR)
        while current_seek < header_list_sentinel:
            file_header = FileHeader.from_archive(archive)
            file_header_list.append(file_header)
            current_seek = archive.seek(file_header.header_size, os.SEEK_CUR)

    file_header_list.sort(key=lambda fh: fh.file_path)
    return file_header_list


def _header_path_list_from_paths(*paths: Union[str, bytes, PathLike],
                                 depth: int = 0) -> Tuple[List[FileHeader], List[Union[str, bytes, PathLike]]]:
    """Internal function.

    Used for packing files into an archive, the function parses directories and creates a list of file headers.

    :param paths: Paths argument passed to the pack function.
    :param depth: Should be 0 when called, used for going through directories.
    :return: 2-tuple containing list of file headers and list of paths to files.
    """
    file_header_list = []
    file_path_list = []
    for path in paths:
        path = Path(os.path.abspath(path))
        if not path.exists():
            raise ResourceNonExistentError(str(path))
        else:
            if path.is_file():
                file_header_list.append(FileHeader.from_file(path, depth=depth))
                file_path_list.append(path)
            elif path.is_dir():
                directory_file_header_list, directory_file_path_list = \
                    _header_path_list_from_paths(*path.iterdir(), depth=depth + 1)
                file_header_list.extend(directory_file_header_list)
                file_path_list.extend(directory_file_path_list)
            else:
                raise ResourceCantBeArchivedError(str(path))

    if depth == 0:
        current_offset = len(FILE_SIGNATURE) + sum(map(lambda header: header.header_size, file_header_list))
        for file_header in file_header_list:
            file_header.file_offset = current_offset
            current_offset += file_header.file_size
    return file_header_list, file_path_list


def _create_destination_path(destination_path: Union[str, bytes, PathLike]) -> None:
    """Internal function.

    Used when unpacking an archive, creates the destination path.

    :param destination_path: Path to directory where to unpack.
    """
    destination_path = Path(destination_path)
    if not destination_path.exists():
        destination_path.mkdir(parents=True)
        logging.info(f"created destination_path: {destination_path}")


def _create_file_path(file_path: Union[str, bytes, PathLike]) -> None:
    """Internal function

    Used when unpacking an archive, creates the path to the file.

    :param file_path: Path to the file to be created.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)
            logging.info(f"created file_path.parent: {file_path.parent}")
        file_path.touch()
        logging.info(f"touched file_path: {file_path}")


def _unpack_file(file_header: FileHeader, archive_file_object: BinaryIO) -> None:
    """Internal function.

    Used when unpacking an archive, extracts the file from the archive into the path specified
    in the file header.

    :param file_header: File's header from the archive.
    :param archive_file_object: Archive file object.
    """
    logging.info(f"writing file: {file_header.file_path}")
    with open(file_header.file_path, 'wb') as file:
        archive_file_object.seek(file_header.file_offset, os.SEEK_SET)
        bytes_to_read = file_header.file_size
        while chunk := archive_file_object.read(min(CHUNK_SIZE, bytes_to_read)):
            bytes_to_read -= min(CHUNK_SIZE, bytes_to_read)
            file.write(chunk)
    logging.info(f"wrote file: {file_header.file_path}")
