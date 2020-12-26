import os
import time
from pathlib import Path

from FileHeader import FileHeader


class Cup:
    @staticmethod
    def header_list(archive_path):
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
        file_header_list = Cup.header_list(archive_path)

        print(f'{"File size":12}{"Last access time":25}File')
        for fh in file_header_list:
            print(f'{str(fh.file_size):12}{time.ctime(fh.file_timestamp):25}{fh.file_path}')
        return file_header_list

    @staticmethod
    def full_unpack(archive_path: str, destination_path: str):
        archive_path = Path(archive_path).resolve()
        destination_path = Path(destination_path).resolve()
        previous_working_directory = os.getcwd()

        if not destination_path.exists():
            destination_path.mkdir(parents=True)
            print(f"created {destination_path}")

        os.chdir(destination_path)
        file_header_list = Cup.header_list(archive_path)
        with open(archive_path, 'rb') as archive:
            for file_header in file_header_list:
                file_path = Path(file_header.file_path)
                if not file_path.exists():
                    if not file_path.parent.exists():
                        print(f"created {file_path.parent}")
                        file_path.parent.mkdir(parents=True)
                    file_path.touch()
                    print(f"touched {file_path}")

                with open(file_path, 'wb') as file:
                    archive.seek(file_header.file_offset, os.SEEK_SET)
                    bytes_to_read = file_header.file_size
                    print(bytes_to_read)
                    while chunk := archive.read(min(bytes_to_read, 512)):
                        bytes_to_read -= min(bytes_to_read, 512)
                        print(bytes_to_read)
                        file.write(chunk)

        os.chdir(previous_working_directory)

    @staticmethod
    def unpack(self):
        pass
