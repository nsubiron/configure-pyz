SHELL = sh

APPNAME = configure
SOURCE = source

default: run test

test: dist
	@python test.py bin/$(APPNAME).pyz test_cases

run: dist
	@bin/$(APPNAME).pyz --version

dist: bin/$(APPNAME).pyz

clean:
	@rm -R -f bin

# See http://legacy.python.org/dev/peps/pep-0441/
bin/$(APPNAME).pyz: bin/$(APPNAME).zip
	@echo '#!/usr/bin/env python' | cat - bin/$(APPNAME).zip > bin/$(APPNAME).pyz
	@chmod u+x bin/$(APPNAME).pyz

bin/$(APPNAME).zip: $(SOURCE)/* setup.py
	@mkdir -p bin
	@python setup.py -d -o bin/$(APPNAME).zip source
