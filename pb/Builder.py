"""
Provide ability to build a C/C++ project.

This module provides function build(...),
which takes project information in BuildConfig class,
and builds the project, printing the progress.
Possible build exceptions are handled.
"""

from __future__ import annotations
from enum import Enum, auto
from collections import deque
from pathlib import Path

from pb.BuildElement import *
from pb.Colored import Esc
from pb.CBuildElement import *
from pb.Dependency import read_depfile


class BuildType(Enum):
    release = auto()
    debug = auto()


class BuildAdditionalArgs:
    def __init__(
        self,
        release: list[str],
        debug: list[str],
    ) -> None:
        self.commands = {
            BuildType.release: release,
            BuildType.debug: debug
        }


class CombinedCBuildElements:
    def __init__(
        self,
        requested: CBuildElements,
        debug: CBuildElements
    ) -> None:
        self.requested = requested
        self.debug = debug


class BuildConfig:
    def __init__(
        self,
        build_path: str,
        source_path: str, 
        sources: list[Any],
        libraries: list[str],
        libraries_dirs: list[str],
        target: str,
        additional_args: BuildAdditionalArgs,
        compiler: str,
        build_type: BuildType,
        sources_search_pattern:str|None=None
    ) -> None:
        self.build_path = Path(build_path)
        self.source_path = Path(source_path)
        self.sources = [Path(p) for p in sources]
        self.libraries = libraries
        self.libraries_dirs = [Path(p) for p in libraries_dirs]
        self.target = Path(target)
        self.additional_args = additional_args
        self.compiler = compiler
        self.build_type = build_type
        self.sources_search_pattern = sources_search_pattern

    def toCombinedCBuildElements(self):
        return CombinedCBuildElements(
            self._toCBuildElementsWithBuildType(self.build_type),
            self._toCBuildElementsWithBuildType(BuildType.debug)
        )
    
    def hashes_path(self) -> Path:
        return self.build_path / build_subdirectory(self.build_type) / Path("hashes.json")
    
    def _toCBuildElementsWithBuildType(self, build_type: BuildType):
        objects = [
            CObjectBuildElement(
                (self.source_path / s).with_suffix(".cpp"),
                (self.build_path / build_subdirectory(self.build_type) / s).with_suffix(".o"),
                self.additional_args.commands[build_type],
                self.compiler,
                self.source_path,
                []
            )
            for s in self.sources
        ]
        target = CTargetBuildElement(
                objects,
                self.libraries,
                self.libraries_dirs,
                self.build_path / build_subdirectory(build_type) / self.target,
                self.additional_args.commands[build_type],
                self.compiler,
                self.source_path,
            )
        return CBuildElements(target, objects)


def build_subdirectory(build_type: BuildType):
    if build_type == BuildType.release:
        return pathlib.Path("release")
    if build_type == BuildType.debug:
        return pathlib.Path("debug")
    else:
        raise NotImplementedError


def make_directories(config: BuildConfig, element: BuildElement):
    def f(e: BuildElement):
        e.path.parent.mkdir(parents=True, exist_ok=True)
        for d in e.dependencies:
            f(d)

    config.build_path.mkdir(parents=True, exist_ok=True)
    f(element)


def build(config: BuildConfig) -> bool:
    """Build with config. Return whether build succeeded."""
    if config.sources_search_pattern:
        try:
            config.sources.extend([
                p.resolve().relative_to(config.source_path.resolve()) 
                for p in config.source_path.glob(config.sources_search_pattern)
            ])
        except OSError:
            print(f"{Esc.red_bright}OS Error:{Esc.default} cannot find sources in source directory")

    combined_c_build_elements = config.toCombinedCBuildElements()
    c_build_elements = combined_c_build_elements.requested
    debug_c_build_elements = combined_c_build_elements.debug

    for e in c_build_elements.objects:
        try:
            rules = read_depfile(e.object_file)   
        except OSError as e:
            print(f"{Esc.red_bright}OS Error:{Esc.default} cannot access a depfile, filename {e.filename}")
            return False
        if e.object_file in rules:
            e.headers = rules[e.object_file]

    target_element = c_build_elements.target.toBuildElement()
    make_directories(config, target_element)
    build_queue: deque[BuildElement] = deque()
    try:
        hashes = read_hashes_db(config.hashes_path())
    except OSError as e:
        print(f"{Esc.red_bright}OS Error:{Esc.default} cannot access hash database, filename {e.filename}")
        return False
    hashes_new = Hashes()

    try:
        update_build_queue(target_element, hashes, build_queue, hashes_new)
    except OSError as e:
        print(f"{Esc.red_bright}OS Error:{Esc.default} cannot access a file, filename {e.filename}")
        return False
    hashes = hashes_new

    try:
        write_clang_compilation_database(
            config.build_path / Path("compile_commands.json"),
            debug_c_build_elements
        )
    except OSError as e:
        print(f"{Esc.red_bright}OS Error:{Esc.default} write clang compilation database, filename {e.filename}")
        return False
    
    try:
        execute_build_queue(build_queue, hashes)
    except OSError as e:
        print(f"{Esc.red_bright}OS Error:{Esc.default} cannot access a file, filename {e.filename}")
        return False
    except CommandFailException as e:
        print(f"{Esc.red_bright}Build failure:{Esc.default} build command failed. The command: {e.command}")
        return False

    try:
        write_hashes_db(config.hashes_path(), hashes)
    except OSError as e:
        print(f"{Esc.red_bright}OS Error:{Esc.default} cannot access hash database, filename {e.filename}")
        return False
    print(f"{Esc.green_bright}Done.{Esc.default}")
    return True
