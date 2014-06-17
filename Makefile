all: test docs
	@true

test:
	adb forward tcp:2828 tcp:2828
	python -m semiauto webapi_tests.semiauto.smoketests | python -m mozlog.structured.scripts.format mach 2>/dev/null

dist:
	python setup.py sdist

clean:
	$(MAKE) -C ./docs clean
	-rm -rf fxos_certsuite.egg-info
	-rm -rf certsuite_venv
	-rm -rf dist
	-rm -rf build
	-rm -rf firefox-os-certification_*.zip

docs: documentation.pdf
	@true

.PHONY = all test dist clean docs

DOCS_SRC = $(shell find ./docs -name '*.rst')

documentation.pdf: $(DOCS_SRC)
	$(MAKE) -C ./docs latexpdf
	cp ./docs/_build/latex/*.pdf $@
