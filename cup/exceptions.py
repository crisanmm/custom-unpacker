"""
Contains custom defined exceptions
"""

import os


class CupException(Exception):
    """ Base custom exception class """
    pass


class ArchiveExistsError(CupException):
    """ Raised when """
    def __init__(self, archive_path):
        super().__init__(f'Archive output file already exists: {os.path.abspath(archive_path)}')
