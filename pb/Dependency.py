"""
Support for reading .d files.
"""

from __future__ import annotations
from pathlib import Path


def read_depfile(element: Path) -> dict[Path, list[Path]]:
    """
    Read the .d file and return dependencies info.
    
    Returns a dict where keys are targets
    and values are lists of dependencies (only the headers).
    """
    dfile_path = element.with_suffix(".d")
    if not dfile_path.is_file():
        return {}
    rules :dict[Path, list[Path]] = {} 
    with open(dfile_path, "rt", encoding="utf-8") as f:
        lines = list(map(str.rstrip, f.readlines()))
    
    i = 0
    while i < len(lines) - 1:
        if lines[i][-1] == "\\":
            lines[i] = lines[i][:-1] + " " + lines[i+1].lstrip()
            lines.pop(i+1)
        else:
            i += 1
    
    for l in lines:
        rule = l.split()
        if len(rule) < 2:
            continue
        rules[Path(rule[0][:-1])] = [Path(d) for d in rule[1:]]
    
    # Filter only the headers
    for rule in rules:
        rules[rule] = list(filter(
            lambda p: p.suffix in [".h", ".hpp"], 
            rules[rule]
        ))

    
    return rules
