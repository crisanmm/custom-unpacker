import os
import time
from pathlib import Path
from os import PathLike
from typing import *

from FileHeader import FileHeader


def _process_renaming(renaming: Sequence[Tuple[Union[int, str], str]],
                      file_header_list: List[FileHeader]) -> Dict[str, str]:
    def map_rename(t):
        original_name, changed_name = t
        if type(original_name) == str:
            return t
        elif type(original_name) == int:
            return file_header_list[original_name - 1].file_path, changed_name

    renaming = map(map_rename, renaming)
    return {original_name: changed_name for original_name, changed_name in renaming}


def _process_file_header_list(renaming: Dict[str, str],
                              file_header_list: List[FileHeader]) -> List[FileHeader]:
    file_header_list = list(filter(lambda fh: fh.file_path in renaming.keys(), file_header_list))
    for file_header in file_header_list:
        file_header.file_path = renaming.get(file_header.file_path)
    return file_header_list


class Cup:
    @staticmethod
    def get_header_list(archive_path: str):
        file_header_list = []

        with open(archive_path, 'rb') as archive:
            file_header = FileHeader.from_archive(archive)
            file_header_list.append(file_header)
            header_list_sentinel = file_header.file_offset

            current_seek = archive.seek(file_header.header_size, os.SEEK_SET)
            while current_seek != header_list_sentinel:
                file_header = FileHeader.from_archive(archive)
                file_header_list.append(file_header)
                current_seek = archive.seek(file_header.header_size, os.SEEK_CUR)

        file_header_list.sort(key=lambda fh: fh.file_path)
        return file_header_list

    @staticmethod
    def create_archive(*file_paths, archive_name="archive.cup"):
        file_header_list = []

        # TODO: migrate to pathlib

        # create headers
        for file_path in file_paths:
            if (Path.cwd() / Path(file_path)).exists():
                # print('file exists')
                file_header_list.append(FileHeader.from_file(file_path))
            else:
                # print("file doesn't exist")
                pass

        # set file offset for each header
        header_size_list = map(lambda header: header.header_size, file_header_list)
        current_offset = sum(header_size_list)
        for file_header in file_header_list:
            # print(current_offset)
            file_header.set_offset(current_offset)
            current_offset += file_header.file_size

        # write headers and files to archive file
        with open(archive_name, 'wb') as archive:
            for file_header in file_header_list:
                archive.write(file_header.header_array)

            for file_path in file_paths:
                with open(file_path, 'rb') as file:
                    while chunk := file.read(1024):
                        archive.write(chunk)

    @staticmethod
    def list(archive_path):
        file_header_list = Cup.get_header_list(archive_path)

        print(f'{"No":3}{"Size":12}{"Last access time":25}Name')
        for index, file_header in enumerate(file_header_list):
            print(
                f"""{str(index + 1):3}{str(file_header.file_size):12}{time.ctime(file_header.file_timestamp):25}{file_header.file_path}""")
        return file_header_list

    @staticmethod
    def unpack(*renaming: Tuple[Union[int, str], str], archive_path: str, destination_path: str):
        archive_path = Path(archive_path).resolve()
        file_header_list = Cup.get_header_list(archive_path)
        previous_working_directory = os.getcwd()

        Cup._create_destination_path(destination_path)

        if renaming:
            renaming = _process_renaming(renaming, file_header_list)
            file_header_list = _process_file_header_list(renaming, file_header_list)

        os.chdir(destination_path)
        with open(archive_path, 'rb') as archive:
            for file_header in file_header_list:
                Cup._create_file_path(file_header.file_path, file_header)
                Cup._unpack_file(file_header.file_path, archive, file_header)
        os.chdir(previous_working_directory)

    @staticmethod
    def _create_destination_path(destination_path: str):
        destination_path = Path(destination_path)
        if not destination_path.exists():
            destination_path.mkdir(parents=True)
            print(f"created {destination_path}")

    @staticmethod
    def _create_file_path(file_path: Union[str, bytes, PathLike], file_header: FileHeader):
        file_path = Path(file_header.file_path)
        if not file_path.exists():
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True)
                print(f"created {file_path.parent}")
            file_path.touch()
            print(f"touched {file_path}")

    @staticmethod
    def _unpack_file(file_path: Path, archive_file_object, file_header: FileHeader):
        with open(file_path, 'wb') as file:
            archive_file_object.seek(file_header.file_offset, os.SEEK_SET)
            bytes_to_read = file_header.file_size
            while chunk := archive_file_object.read(min(512, bytes_to_read)):
                bytes_to_read -= min(512, bytes_to_read)

                file.write(chunk)
