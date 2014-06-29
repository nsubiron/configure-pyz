default: projects

projects:
	python tools/configure.py source

clean:
	@rm -f -R build

clean-all: clean
	@rm -f -R bin
	@rm -f graph.pdf
	@rm -f build.ninja

graph:
	ninja -t graph | dot -Tpdf -ograph.pdf
