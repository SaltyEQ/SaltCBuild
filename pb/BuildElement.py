"""
Provide ability to build an element only when needed using hashes.

Class BuildElement represents something being built,
and function update_build_queue() allows
to generate a queue of build commands,
building only elements with changed sources, or build commands,
or dependencies.
This relies on comparing file and command hashes with previous built.
This module allows to keep the hashes in a json database.
The build queue can be executed with execute_build_queue() function.
"""

from __future__ import annotations
from typing import Any
from collections import deque
from pathlib import Path
import hashlib
import json
import subprocess

from pb.Colored import Esc


class BuildElement:
    """
    Class represents a file being built. (Not aware of the language)
    
    Fields:
    - path: Path - Path to the file being operated on
    - build_command: str - Command for building the file
    - dependencies: List[BuildElement] - If any of these change,
        the file has to be rebuilt
    """

    def __init__(self, path: Path, build_command: str, dependencies: list[BuildElement]) -> None:
        self.path = path
        self.build_command = build_command
        self.dependencies = dependencies


class Hashes:
    """
    Class storing hashes of files and build commands.
    Fields:
    - file_hashes: Dict[Path, str] - Hashes of files
    - command_hashes: Dict[Path, str] - Hashes of commands

    Methods:
    - to_obj() -> Any - Represent as a json object
    - from_obj(j: Any) - Read from a json object
    """
    def __init__(self) -> None:
        self.file_hashes: dict[Path, str] = dict()
        self.command_hashes: dict[Path, str] = dict()
    
    def to_obj(self) -> Any:
        """Represent as a json object"""
        j = dict()
        j["files"] = {str(k): v for k, v in self.file_hashes.items()}
        j["commands"] = {str(k): v for k, v in self.command_hashes.items()}
        return j
    
    def from_obj(self, j: Any):
        """Read from a json object"""
        self.file_hashes = {Path(k): v for k, v in dict(j["files"]).items()}
        self.command_hashes = {Path(k): v for k, v in dict(j["commands"]).items()}


def update_build_queue(element: BuildElement, hashes: Hashes, build_queue: deque[BuildElement], hashes_new: Hashes):
    """
    Update the build queue with necessary build commands.

    This function recursively checks for changes 
    in elements' file and command hashes and in dependencies.
    Also the hashes get copied to hashes_new, but only for elements
    present in the dependency tree.
    Can raise.
    """
    dependencies_should_build = False
    if element.dependencies:
        for dependency in element.dependencies:
            d = update_build_queue(dependency, hashes, build_queue, hashes_new)
            dependencies_should_build = dependencies_should_build or d
    should_build = dependencies_should_build
    # Note that command_hash_changed() and file_hash_changed() update hashes_new,
    # and we have to always execute them for all of the elements.
    should_build = command_hash_changed(element, hashes, hashes_new) or should_build
    should_build = file_hash_changed(element, hashes, hashes_new) or should_build
    if should_build:
        build_queue.appendleft(element)
        return True
    return False


def get_file_hash(path: Path):
    """Return the hash of the file. Can raise."""
    # If the file does not exist, we treat the file
    # as having empty cash
    if not path.is_file():
        return hashlib.md5(bytes("", "utf-8")).hexdigest()
    with open(path, "rb") as f:
        file_hash = hashlib.file_digest(f, "md5").hexdigest()
    return file_hash

def get_command_hash(command: str):
    """Return the hash of the command."""
    return hashlib.md5(bytes(command, "utf-8")).hexdigest()

def read_hashes_db(path: Path):
    hashes = Hashes()
    if not path.is_file():
        return hashes
    with open(path, "rt", encoding="utf-8") as f:
        hashes.from_obj(json.load(f))
    return hashes

def write_hashes_db(path: Path, hashes: Hashes):
    """Write the hashes to the database. Can raise.
    Create the file, if it does not exist."""
    with open(path, "wt", encoding="utf-8") as f:
        json.dump(hashes.to_obj(), f, indent=2)

def command_hash_changed(element: BuildElement, hashes: Hashes, hashes_new: Hashes) -> bool:
    """
    Check the element's build command hash against the hashes.

    Can throw.
    Also add the element's hash to the hashes_new.
    """
    current_hash = get_command_hash(element.build_command)
    hashes_new.command_hashes[element.path] = current_hash
    return ((element.path not in hashes.command_hashes) 
            or (current_hash != hashes.command_hashes[element.path]))

def file_hash_changed(element: BuildElement, hashes: Hashes, hashes_new: Hashes) -> bool:
    """
    Check the element's file hash against the hashes.

    Can throw.
    Also add the command's hash to the hashes_new.
    """
    current_hash = get_file_hash(element.path)
    hashes_new.file_hashes[element.path] = current_hash
    return ((element.path not in hashes.file_hashes) 
            or (current_hash != hashes.file_hashes[element.path]))


class CommandFailException(Exception):
    def __init__(self, command:str|None=None,  *args: object) -> None:
        super().__init__()
        self.command = command


def execute_build_queue(build_queue: deque[BuildElement], hashes: Hashes):
    """
    Execute the build queue and return new hashes.

    May throw an exception.
    """
    while build_queue:
        element = build_queue.pop()
        if element.build_command != "":
            try:
                print(f'{Esc.dim}building {str(element.path)}: {element.build_command}{Esc.n_dim}')
                r = subprocess.run(element.build_command, capture_output=True, encoding="utf-8", shell=True)
            except OSError:
                raise CommandFailException(element.build_command)
            if r.returncode != 0:
                print(r.stderr)
                raise CommandFailException(element.build_command)
            if (r.stdout):
                print(r.stdout)
        hashes.command_hashes[element.path] = get_command_hash(element.build_command)
        hashes.file_hashes[element.path] = get_file_hash(element.path)

