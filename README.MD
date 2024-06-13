# SaltCBuild - an experimental Python script for building C++ projects.

**EXPERIMENTAL**

## What

This program builds a C++ project, as an alternative to Make/Cmake.

Main function is contained in build.py file,
logic - in /bp/ directory.
/src contains example C++ code being built.
Build output files go to /build/ directory.

To build run build.py

## Why

Make has a rather weird syntax (just my taste), and is not aware of C++.
And it either requires using wildcards (which I don't want), 
or doesn't do much to help except for knowing what needs to be rebuilt or not.

Cmake is powerful, but also very complex. It's good when it works, 
but I had hard time troubleshooting it.

Not saying those are bad instruments, I just had reasons to try
to homebrew something.

## Features

- Uses clang++ (and can use any other compiler)
- Support different commands for debug and release
- Check which sources are changed to avoid unnecessary rebuilds
- Use .d files produced by the compiler to figure out header dependencies
- Produce JSON compilation database for clangd
