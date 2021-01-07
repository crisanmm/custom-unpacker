"""
Contains custom defined exceptions
"""

import os


class CupException(Exception):
    """Base custom exception class."""
    pass


class ArchiveAlreadyExistsError(CupException):
    """Raised when"""

    def __init__(self, archive_path):
        super().__init__(f"Archive output file already exists: {os.path.abspath(archive_path)}")


class ResourceNonExistentError(CupException):
    """"""

    def __init__(self, resource_path):
        super().__init__(f"Resource doesn't exist: {resource_path}")


class ResourceCantBeArchivedError(CupException):
    """"""

    def __init__(self, resource_path):
        super().__init__(f"Resource is not a file/directory: {resource_path}")


class ArchiveNonExistentError(CupException):
    """"""

    def __init__(self, archive_path):
        super().__init__(f"Archive doesn't exist: {archive_path}")


class ArchiveNotRecognizableError(CupException):
    """"""

    def __init__(self, archive_path):
        super().__init__(f"File is not a CUP archvie: {archive_path}")