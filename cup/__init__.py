"""
Cup (Custom Unpacker-Packer) is an archiver without compression.

Cup is used to pack multiple files or directories into a single .cup file known as an archive.
Cup also supports functionality for getting information from such a .cup file as well as unpacking
a .cup file to get its original contents.
"""

from .archiver import pack, unpack, info

__all__ = ["pack", "unpack", "info"]
