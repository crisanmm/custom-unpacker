"""
Contains custom defined exceptions
"""

import os


class CupException(Exception):
    """Base custom exception class."""
    pass


class ArchiveAlreadyExistsError(CupException):
    """Raise error when the output archive is also a resource to be archived.

    For example, let's take the case when the output archive is `output_ar.cup` and we are also trying
    to archive `output_ar.cup`. In that case we can be stuck in an infinite loop where we keep reading and writing
    to the same file.
    """

    def __init__(self, archive_path):
        super().__init__(f"Archive output file already exists: {os.path.abspath(archive_path)}")


class ResourceNonExistentError(CupException):
    """Raise error when the path to a resource to archive doesn't exist."""

    def __init__(self, resource_path):
        super().__init__(f"Resource doesn't exist: {resource_path}")


class ResourceCantBeArchivedError(CupException):
    """Raise error when the resource to archive is not a file/directory."""

    def __init__(self, resource_path):
        super().__init__(f"Resource is not a file/directory: {resource_path}")


class ArchiveNonExistentError(CupException):
    """Raise error when path to archive doesn't exist."""

    def __init__(self, archive_path):
        super().__init__(f"Archive doesn't exist: {archive_path}")


class ArchiveNotRecognizableError(CupException):
    """Raise error when archive doesn't have the Cup file signature."""

    def __init__(self, archive_path):
        super().__init__(f"File is not a Cup archive: {archive_path}")
