default: projects

projects:
	python tools/configure.py source

clean:
	@rm -f -R build

clean-all: clean
	@rm -f -R bin
	@rm -f build.ninja
