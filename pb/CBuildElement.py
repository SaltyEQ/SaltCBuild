"""
Provide support for C/C++ build units.

This module provides representations of C objects and targets,
including their build commands and dependencies.
These classes can be translated to BuildElement.
"""
from __future__ import annotations
from typing import List
import pathlib
import json

from pb.BuildElement import BuildElement

class ClangCommandObject:
    def __init__(
        self, 
        file: pathlib.Path,
        command: List[str],
    ) -> None:
        self.file = file
        self.command = command
    
    def to_json(self):
        return {
            "directory": ".",
            "arguments": self.command,
            "file": str(self.file.resolve())
        }

class CObjectBuildElement:
    def __init__(
        self, 
        source: pathlib.Path,
        object_file: pathlib.Path,
        additional_args: List[str],
        compiler: str,
        source_dir: pathlib.Path,
        headers: List[pathlib.Path]
    ) -> None:
        self.source = source
        self.object_file = object_file
        self.additional_args = additional_args
        self.compiler = compiler
        self.source_dir = source_dir
        self.headers = headers
    
    def command(self) -> List[str]:
        s = []
        s.append(self.compiler)
        s.extend(self.additional_args)
        s.append(f'-I"{self.source_dir.resolve()}"')
        s.extend(("-c", f'"{str(self.source)}"'))
        s.extend(("-o", f'"{str(self.object_file)}"'))
        return s
    
    def toClangCommandObject(self):
        return ClangCommandObject(
            self.source,
            self.command()
        )
    
    def toBuildElement(self):
        header_elements = [BuildElement(h, "", []) for h in self.headers]
        return BuildElement(
            self.object_file,
            " ".join(self.command()),
            [BuildElement(self.source, "", [])] + header_elements
        )


class CTargetBuildElement:
    def __init__(
        self,
        objects: List[CObjectBuildElement],
        libraries: List[str],
        libraries_dirs: List[pathlib.Path],
        target: pathlib.Path,
        additional_args: List[str],
        compiler: str,
        source_dir: pathlib.Path,
    ) -> None:
        self.objects = objects
        self.libraries = libraries
        self.libraries_dirs = libraries_dirs
        self.target = target
        self.additional_args = additional_args
        self.compiler = compiler
        self.source_dir = source_dir

    def command(self) -> List[str]:
        s = []
        s.append(self.compiler)
        s.extend(self.additional_args)
        s.extend((f'"{str(o.object_file)}"' for o in self.objects))
        s.extend((f'-L"{str(l)}"' for l in self.libraries_dirs))
        s.extend((f'-l:{l}' for l in self.libraries))
        s.extend(("-o", f'"{str(self.target)}"'))
        return s
    
    def toClangCommandObject(self):
        return ClangCommandObject(
            self.objects[0].object_file,
            self.command(),
        )
    
    def toBuildElement(self):
        return BuildElement(
            self.target,
            " ".join(self.command()),
            [a.toBuildElement() for a in self.objects]
        )

class CBuildElements:
    def __init__(
        self, 
        target: CTargetBuildElement,
        objects: List[CObjectBuildElement],
    ) -> None:
        self.target = target
        self.objects = objects
    

def write_clang_compilation_database(path: pathlib.Path, elements: CBuildElements):
    unit_list = []
    for e in elements.objects:
        unit_list.append(e.toClangCommandObject().to_json())
    unit_list.append(
        elements.target
        .toClangCommandObject().to_json()
    )
    with open(path, "wt", encoding="utf-8") as f:
        json.dump(unit_list, f, indent=2)
