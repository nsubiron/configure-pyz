default: build

.PHONY: configure sublime doxygen

CONFIG = python tools/configure.py -f tools/settings.json

configure:
	@$(CONFIG) --ninja

sublime:
	@$(CONFIG) --sublime

codeblocks:
	@$(CONFIG) --codeblocks

build: configure
	@ninja

all: sublime
	@ninja all doxygen

clean:
	@ninja -t clean

graph: configure
	@ninja -t graph | dot -Tpdf -ograph.pdf

doxygen: configure
	@ninja doxygen
