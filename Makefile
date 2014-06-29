all: projects build

.PHONY: build.ninja

build.ninja:
	@echo Generating ninja files ...
	@python tools/configure.py source

projects: build.ninja
	@echo Generating projects ...
	@mkdir -p projects
	@ninja -t targets | python tools/project_generator.py > projects/ninja-cpp11.sublime-project

build: build.ninja
	@echo Building targets ...
	@ninja

clean:
	@rm -f -R build

clean-all: clean
	@rm -f -R bin
	@rm -f -R projects
	@rm -f graph.pdf
	@rm -f build.ninja

graph:
	ninja -t graph | dot -Tpdf -ograph.pdf
