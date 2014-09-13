default: projects build

all: projects build graph doxygen

.PHONY: build.ninja doxygen

ifdef DEBUG
  DFLAG = -d
  DTAG = " DEBUG"
endif

build.ninja:
	@echo Generating$(DTAG) ninja files ...
	@python tools/configure.py $(DFLAG) source

projects: build.ninja
	@echo Generating projects ...
	@mkdir -p projects
	@ninja -t targets | \
	    python tools/project_generator.py $(DFLAG) $(DEBUG) > \
	    projects/ninja-cpp11.sublime-project

build: build.ninja
	@echo Building targets ...
	@ninja

clean:
	@ninja -t clean

clean-all:
	@rm -f -R bin
	@rm -f -R build
	@rm -f -R projects
	@rm -f graph.pdf
	@rm -f build.ninja

graph:
	@ninja -t graph | dot -Tpdf -ograph.pdf

build/Doxyfile: tools/Doxyfile
	@mkdir -p build
	@cat tools/Doxyfile | \
	    sed s/$$\{project_name\}/\"Ninja\ C++11\"/ | \
	    sed s/$$\{input_dir\}/source/ | \
	    sed s/$$\{output_dir\}/build/ > \
	    build/Doxyfile

doxygen: build/Doxyfile
	@echo Building documentation ...
	@doxygen build/Doxyfile
