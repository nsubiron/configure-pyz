default: build

.PHONY: configure projects doxygen

CONFIG = python tools/configure.py -f tools/settings.json

configure:
	@echo Configure...
	@$(CONFIG) --ninja

projects:
	@echo Configure...
	@$(CONFIG) --sublime

codeblocks:
	@echo Configure...
	@$(CONFIG) --codeblocks

build: configure
	@echo Building targets...
	@ninja

all: projects
	@echo Building targets...
	@ninja all doxygen

clean:
	@ninja -t clean

graph: configure
	@ninja -t graph | dot -Tpdf -ograph.pdf

doxygen: configure
	@ninja doxygen
