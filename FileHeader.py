import os
from os import PathLike
from pathlib import Path
from typing import *
from typing import BinaryIO

BYTES_FOR = {
    "offset": 8,
    "timestamp": 4,
    "file_size": 4,
    "file_path_length": 2,
}


class FileHeader:
    def __init__(self):
        self.header_array = bytearray()

    @property
    def header_size(self) -> int:
        return len(self.header_array)

    @property
    def file_offset(self) -> int:
        return int.from_bytes(self.header_array[0:8], 'little')

    @file_offset.setter
    def file_offset(self, offset: int) -> None:
        offset_bytes = offset.to_bytes(BYTES_FOR['offset'], 'little')
        self.header_array[0:8] = offset_bytes

    @property
    def file_timestamp(self) -> int:
        return int.from_bytes(self.header_array[8:12], 'little')

    @file_timestamp.setter
    def file_timestamp(self, timestamp: float) -> None:
        # timestamp is float, convert it to int
        timestamp = int(timestamp)
        timestamp_bytes = timestamp.to_bytes(BYTES_FOR['timestamp'], 'little')
        self.header_array[8:12] = timestamp_bytes

    @property
    def file_size(self) -> int:
        return int.from_bytes(self.header_array[12:16], 'little')

    @file_size.setter
    def file_size(self, file_size: int) -> None:
        file_size_bytes = file_size.to_bytes(BYTES_FOR['file_size'], 'little')
        self.header_array[12:16] = file_size_bytes

    @property
    def file_path_length(self) -> int:
        return int.from_bytes(self.header_array[16:18], 'little')

    @file_path_length.setter
    def file_path_length(self, file_path_length: int) -> None:
        file_path_length_bytes = file_path_length.to_bytes(BYTES_FOR['file_path_length'], 'little')
        self.header_array[16:18] = file_path_length_bytes

    @property
    def file_path(self) -> str:
        return self.header_array[18:18 + self.file_path_length].decode()

    @file_path.setter
    def file_path(self, file_path) -> None:
        file_path = str(file_path)
        bytes_for_file_path = len(file_path)
        self.header_array[18:18 + bytes_for_file_path] = file_path.encode()

    @staticmethod
    def from_archive(archive: BinaryIO, header_position: int = 0) -> 'FileHeader':
        """
        Get a FileHeader object from an opened archive.
        Used for listing or unpacking the archive.

        :param archive: The archive file object
        :param header_position:
         The header position relative to the beginning of the archive file
        :return: FileHeader object
        """
        original_seek = archive.seek(0, os.SEEK_CUR)

        file_header = FileHeader()
        archive.seek(header_position + 16, os.SEEK_CUR)
        bytes_for_file_path = int.from_bytes(archive.read(2), 'little')
        archive.seek(original_seek, os.SEEK_SET)
        header_size = sum(BYTES_FOR.values()) + bytes_for_file_path
        file_header.header_array = bytearray(archive.read(header_size))

        archive.seek(original_seek, os.SEEK_SET)
        return file_header

    @staticmethod
    def from_file(file_path: Union[str, bytes, PathLike], depth: int = 0) -> 'FileHeader':
        file_path = Path(file_path).resolve()
        file_path_relative = file_path.resolve().name
        if depth > 0:
            for directory in reversed(file_path.parts[-depth - 1:-1]):
                file_path_relative = Path(directory) / file_path_relative

        file_header = FileHeader()
        header_array_size = sum(BYTES_FOR.values()) + len(str(file_path_relative))
        file_header.header_array = bytearray(header_array_size)
        file_header.file_timestamp = file_path.stat().st_mtime
        file_header.file_size = file_path.stat().st_size
        file_header.file_path_length = len(str(file_path_relative))
        file_header.file_path = file_path_relative
        return file_header
