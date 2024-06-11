from __future__ import annotations
import pathlib
import hashlib
import json
import subprocess
from typing import List
from collections import deque
from pb.colored import Esc


class BuildElement:
    def __init__(self, path: pathlib.Path, build_command: str, dependencies: List[BuildElement]) -> None:
        self.path = path
        self.build_command = build_command
        self.dependencies = dependencies


class Hashes:
    def __init__(self) -> None:
        self.file_hashes = dict()
        self.command_hashes = dict()
    
    def to_obj(self):
        j = dict()
        j["files"] = {str(k): v for k, v in self.file_hashes.items()}
        j["commands"] = {str(k): v for k, v in self.command_hashes.items()}
        return j
    
    def from_obj(self, j):
        self.file_hashes = {pathlib.Path(k): v for k, v in dict(j["files"]).items()}
        self.command_hashes = {pathlib.Path(k): v for k, v in dict(j["commands"]).items()}


def update_build_queue(element: BuildElement, hashes: Hashes, build_queue: deque[BuildElement], hashes_new: Hashes):
    """
    If last, check for file hash and command hash.
    If mismatch, add to the build queue, and return true.
    If not last, get children result.
    If any of children, or file hash, or command mismatch, return false
    and add to the queue.
    Else return true.
    Can throw an exception.
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


def get_file_hash(path: pathlib.Path):
    """Return hash of the file. May throw an exception."""
    # If the file does not exist, we treat the file
    # as having empty cash
    if not path.is_file():
        return hashlib.md5(bytes("", "utf-8")).hexdigest()
    with open(path, "rb") as f:
        file_hash = hashlib.file_digest(f, "md5").hexdigest()
    return file_hash

def get_command_hash(command: str):
    """Return hash of the command."""
    return hashlib.md5(bytes(command, "utf-8")).hexdigest()

def read_hashes_db(path: pathlib.Path):
    hashes = Hashes()
    if not path.is_file():
        return hashes
    with open(path, "rt", encoding="utf-8") as f:
        hashes.from_obj(json.load(f))
    return hashes

def write_hashes_db(path: pathlib.Path, hashes: Hashes):
    """Write the hashes to the database. May throw an exception.
    Create the file, if it does not exist."""
    with open(path, "wt", encoding="utf-8") as f:
        json.dump(hashes.to_obj(), f, indent=2)

def command_hash_changed(element: BuildElement, hashes: Hashes, hashes_new: Hashes):
    """Check the element's build command hash against the hashes
    and return the result. Can throw an exception.
    Also add the element's hash to the hashes_new."""
    current_hash = get_command_hash(element.build_command)
    hashes_new.command_hashes[element.path] = current_hash
    return ((element.path not in hashes.command_hashes) 
            or (current_hash != hashes.command_hashes[element.path]))

def file_hash_changed(element: BuildElement, hashes: Hashes, hashes_new: Hashes):
    """Check the element's file hash against the hashes
    and return the result. Can throw an exception.
    Also add the command's hash to the hashes_new."""
    current_hash = get_file_hash(element.path)
    hashes_new.file_hashes[element.path] = current_hash
    return ((element.path not in hashes.file_hashes) 
            or (current_hash != hashes.file_hashes[element.path]))


def check_command(command: str):
    return True # TODO: WARNING:

class CommandFailException(Exception):
    def __init__(self, command=None,  *args: object) -> None:
        super().__init__()
        self.command = command

class CommandIllegalException(Exception):
    def __init__(self, command=None,  *args: object) -> None:
        super().__init__()
        self.command = command


def execute_build_queue(build_queue: deque[BuildElement], hashes: Hashes):
    """Execute the build queue and return the hashes.
    May throw an exception."""
    while build_queue:
        element = build_queue.pop()
        if element.build_command != "":
            if not check_command(element.build_command):
                raise CommandIllegalException(element.build_command)
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

