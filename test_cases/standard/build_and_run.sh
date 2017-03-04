#!/bin/bash
source ../header.include

$CONFIGURE_PYZ -f tools/configure.json --makefile

make embed
make debug
./build/bin_debug/myexe

make release
./bin/myexe

make targets
make sublime
make codeblocks
make doxygen

rm -Rf bin build projects
rm -f build.ninja Makefile
find . -regex '.*EmbeddedData\.\(h\|cpp\)' -delete
