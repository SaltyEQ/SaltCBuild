"""
This file contains project configuration and main().
"""

from __future__ import annotations
import sys

from pb.BuildElement import *
from pb.Builder import BuildAdditionalArgs, BuildConfig, BuildType, build
from pb.CBuildElement import *


config = BuildConfig(
    build_path="build",
    source_path="src",
    sources=[
        "number_of_day",
        "main"
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
    build_type=BuildType.release
)


if __name__ == "__main__":
    build_argument = sys.argv[1] if len(sys.argv) > 1 else None
    
    if build_argument == None or build_argument == "release":
        config.build_type = BuildType.release
    elif build_argument == "debug":
        config.build_type = BuildType.debug
    else:
        print("Unknown build type.")
        sys.exit()
    
    build(config)
