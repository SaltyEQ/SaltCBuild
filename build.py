"""
This file contains project configuration and main().
"""

from __future__ import annotations
import sys

from pb.BuildElement import *
from pb.Builder import BuildAdditionalArgs, BuildConfig, BuildType, build, delete_build
from pb.CBuildElement import *


config = BuildConfig(
    build_path="build",
    source_path="src",
    sources=[
        
    ],
    libraries=[

    ],
    libraries_dirs=[

    ],
    target="main",
    additional_args=BuildAdditionalArgs(
        release=["-std=c++20", "-MMD"],
        debug=["-g", "-glldb", "-std=c++20", "-MMD"]
    ),
    compiler="clang++",
    build_type=BuildType.release,
    sources_search_pattern="**/*.cpp"
)


if __name__ == "__main__":
    args = sys.argv[1:]
    for arg in args:
        if arg not in ("clean", "release", "debug"):
            print(f"Unrecognized option {arg}, build is cancelled.")
            sys.exit(1)
    
    should_clean = ("clean" in args)
    should_build = (
        "debug" in args 
        or "release" in args 
        or len(args) == 0
    )

    if "release" in args:
        config.build_type = BuildType.release
    else:
        config.build_type = BuildType.debug
    
    if should_clean:
        r = delete_build(config)
        if r is not True:
            sys.exit(1)
    if should_build:
        r = build(config)
        if r is not True:
            sys.exit(1)
