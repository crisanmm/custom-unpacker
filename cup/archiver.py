"""
Provides the main functionality of Cup.
"""

from pathlib import Path
from os import PathLike
from typing import *
from typing import BinaryIO

from .fileheader import FileHeader
from .exceptions import *

CHUNK_SIZE = 4096


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
    file_header_list, file_path_list = _header_list_from_paths(*paths)
    if Path(os.path.abspath(archive_name)) in file_path_list:
        raise ArchiveExistsError(archive_name)

    with open(archive_name, 'wb') as archive:
        for file_header in file_header_list:
            archive.write(file_header.header_array)
        for path in file_path_list:
            with open(path, 'rb') as file:
                while chunk := file.read(CHUNK_SIZE):
                    archive.write(chunk)


def info(archive_path: Union[str, bytes, PathLike]) -> List[Tuple[int, int, int, str]]:
    file_header_list = _header_list_from_archive(archive_path)

    # print(f'{"No":5}{"Size":12}{"Last access time":25}Name')
    # f"""{str(index + 1):5}{str(fh.file_size):12}{time.ctime(fh.file_timestamp):25}{fh.file_path}"""
    file_info_list = []
    for index, fh in enumerate(file_header_list):
        file_info_list.append((index, fh.file_size, fh.file_timestamp, fh.file_path))
    return file_info_list


def unpack(*renaming: Tuple[Union[int, str], str],
           archive_path: Union[str, bytes, PathLike],
           destination_path: Union[str, bytes, PathLike]) -> None:
    archive_path = Path(archive_path).resolve()
    file_header_list = _header_list_from_archive(archive_path)
    previous_working_directory = os.getcwd()

    _create_destination_path(destination_path)

    if renaming:
        renaming = _resolve_renaming(renaming, file_header_list)
        file_header_list = _resolve_file_header_list(renaming, file_header_list)

    os.chdir(destination_path)
    with open(archive_path, 'rb') as archive:
        for file_header in file_header_list:
            _create_file_path(file_header.file_path)
            _unpack_file(file_header, archive)
    os.chdir(previous_working_directory)


def _resolve_renaming(renaming: Sequence[Tuple[Union[int, str], str]],
                      file_header_list: List[FileHeader]) -> Dict[str, str]:
    def map_rename(t):
        original_name, changed_name = t
        if type(original_name) == str:
            return t
        elif type(original_name) == int:
            return file_header_list[original_name - 1].file_path, changed_name

    renaming = map(map_rename, renaming)
    return {original_name: changed_name for original_name, changed_name in renaming}


def _resolve_file_header_list(renaming: Dict[str, str],
                              file_header_list: List[FileHeader]) -> List[FileHeader]:
    file_header_list = list(filter(lambda fh: fh.file_path in renaming.keys(), file_header_list))
    for file_header in file_header_list:
        file_header.file_path = renaming.get(file_header.file_path)
    return file_header_list


def _header_list_from_archive(archive_path: Union[str, bytes, PathLike]) -> List[FileHeader]:
    file_header_list = []
    with open(archive_path, 'rb') as archive:
        file_header = FileHeader.from_archive(archive)
        file_header_list.append(file_header)
        header_list_sentinel = file_header.file_offset

        current_seek = archive.seek(file_header.header_size, os.SEEK_SET)
        while current_seek < header_list_sentinel:
            file_header = FileHeader.from_archive(archive)
            file_header_list.append(file_header)
            current_seek = archive.seek(file_header.header_size, os.SEEK_CUR)

    file_header_list.sort(key=lambda fh: fh.file_path)
    return file_header_list


def _header_list_from_paths(*paths: Union[str, bytes, PathLike],
                            depth: int = 0) -> Tuple[List[FileHeader], List[Union[str, bytes, PathLike]]]:
    file_header_list = []
    file_path_list = []
    for path in paths:
        path = Path(os.path.abspath(path))
        if path.exists():
            if path.is_file():
                file_header_list.append(FileHeader.from_file(path, depth=depth))
                file_path_list.append(path)
            elif path.is_dir():
                directory_file_header_list, directory_file_path_list = \
                    _header_list_from_paths(*path.iterdir(), depth=depth + 1)
                file_header_list.extend(directory_file_header_list)
                file_path_list.extend(directory_file_path_list)
        else:
            pass

    if depth == 0:
        current_offset = sum(map(lambda header: header.header_size, file_header_list))
        for file_header in file_header_list:
            file_header.file_offset = current_offset
            current_offset += file_header.file_size
    return file_header_list, file_path_list


def _create_destination_path(destination_path: Union[str, bytes, PathLike]) -> None:
    destination_path = Path(destination_path)
    if not destination_path.exists():
        destination_path.mkdir(parents=True)
        print(f"created {destination_path}")


def _create_file_path(file_path: Union[str, bytes, PathLike]) -> None:
    file_path = Path(file_path)
    if not file_path.exists():
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)
            print(f"created {file_path.parent}")
        file_path.touch()
        print(f"touched {file_path}")


def _unpack_file(file_header: FileHeader, archive_file_object: BinaryIO) -> None:
    with open(file_header.file_path, 'wb') as file:
        archive_file_object.seek(file_header.file_offset, os.SEEK_SET)
        bytes_to_read = file_header.file_size
        while chunk := archive_file_object.read(min(CHUNK_SIZE, bytes_to_read)):
            bytes_to_read -= min(CHUNK_SIZE, bytes_to_read)
            file.write(chunk)
