#!/bin/bash
source ../header.include

rm -Rf bin build projects source
rm -f build.ninja Makefile configure.yaml

$CONFIGURE_PYZ -d --hello-world

make debug
./build/bin_debug/hello_world

make release
./bin/hello_world

make sublime
make codeblocks
make doxygen

make clean
make all
./build/bin_debug/hello_world
./bin/hello_world
