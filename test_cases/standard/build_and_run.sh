#!/bin/bash
source ../header.include

rm -Rf bin build projects
rm -f build.ninja Makefile configure.yaml
find . -regex '.*embedded_data\.\(h\|cpp\)' -delete

$CONFIGURE_PYZ -d -g --targets --makefile

make embed
make debug
./build/bin_debug/myexe

make release
./bin/myexe

make sublime
make codeblocks
make doxygen

make clean
make all
./build/bin_debug/myexe
./bin/myexe

$CONFIGURE_PYZ -d -f configure.variant.yaml --targets --makefile

make embed
make debug
./build/variant/bin_debug/myexe

make release
./build/variant/bin_release/myexe

make sublime
make codeblocks
make doxygen

make clean
make all
./build/variant/bin_debug/myexe
./build/variant/bin_release/myexe
