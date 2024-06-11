from __future__ import annotations
from pathlib import Path
from typing import Dict, List

def read_depfile(element: Path) -> Dict[Path, List[Path]]:
    dfile_path = element.with_suffix(".d")
    if not dfile_path.is_file():
        return {}
    rules :Dict[Path, List[Path]] = {} 
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
    
    return rules


