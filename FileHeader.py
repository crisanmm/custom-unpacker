import os
from os import path

BYTES_FOR = {
    "offset": 8,
    "timestamp": 4,
    "file_size": 4,
    "file_path_length": 2,
}


class FileHeader:
    def __init__(self):
        self.header_size = int()
        self.header_array = bytearray()

    def set_offset(self, offset: int):
        offset_bytes = offset.to_bytes(BYTES_FOR['offset'], 'little')
        self.header_array[0:8] = offset_bytes

    def _set_timestamp(self, timestamp: float):
        # timestamp is float, convert it to int
        timestamp = int(timestamp)
        timestamp_bytes = timestamp.to_bytes(BYTES_FOR['timestamp'], 'little')
        self.header_array[8:12] = timestamp_bytes

    def _set_file_size(self, file_size: int):
        file_size_bytes = file_size.to_bytes(BYTES_FOR['file_size'], 'little')
        self.header_array[12:16] = file_size_bytes

    def _set_file_path_length(self, file_path_length: int):
        file_path_length_bytes = file_path_length.to_bytes(
            BYTES_FOR['file_path_length'], 'little')
        self.header_array[16:18] = file_path_length_bytes

    def _set_file_path(self, file_path: str):
        file_path_bytes = file_path.encode()
        file_path_length = len(file_path)
        self.header_array[18:18 + file_path_length] = file_path_bytes

    @property
    def file_offset(self):
        return int.from_bytes(self.header_array[0:8], 'little')

    @property
    def file_timestamp(self):
        return int.from_bytes(self.header_array[8:12], 'little')

    @property
    def file_size(self):
        return int.from_bytes(self.header_array[12:16], 'little')

    @property
    def file_path_length(self):
        return int.from_bytes(self.header_array[16:18], 'little')

    @property
    def file_path(self):
        return self.header_array[18:18 + self.file_path_length].decode()

    @file_path.setter
    def file_path(self, value):
        bytes_for_file_path = len(value)
        new_header_array_size = sum(BYTES_FOR.values()) + bytes_for_file_path
        new_header_array = bytearray(new_header_array_size)
        new_header_array[0:16] = self.header_array[0:16]

        self.header_size = new_header_array_size
        self.header_array = new_header_array
        self._set_file_path_length(bytes_for_file_path)
        self._set_file_path(value)

    @staticmethod
    def from_archive(archive, header_position: int = 0):
        """
        Get a FileHeader object from an opened archive.
        Used for listing or unpacking the archive.

        :param archive: The archive file object
        :param header_position:
         The header position relative to the beginning of the archive file
        :return: FileHeader object
        """
        original_seek = archive.seek(0, os.SEEK_CUR)

        fh = FileHeader()
        archive.seek(header_position + 16, os.SEEK_CUR)
        bytes_for_file_path = int.from_bytes(archive.read(2), 'little')
        archive.seek(original_seek, os.SEEK_SET)
        fh.header_size = sum(BYTES_FOR.values()) + bytes_for_file_path
        fh.header_array = bytearray(archive.read(fh.header_size))

        archive.seek(original_seek, os.SEEK_SET)
        return fh

    @staticmethod
    def from_file(file_path):
        fh = FileHeader()
        bytes_for_file_path = len(file_path)
        fh.header_size = sum(BYTES_FOR.values()) + bytes_for_file_path
        fh.header_array = bytearray(fh.header_size)

        fh._set_timestamp(path.getatime(file_path))
        fh._set_file_size(path.getsize(file_path))
        fh._set_file_path_length(len(file_path))
        fh._set_file_path(file_path)
        return fh
