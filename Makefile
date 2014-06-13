all: docs
	@true

clean:
	$(MAKE) -C ./docs clean
	-rm -rf fxos_certsuite.egg-info
	-rm -rf certsuite_venv
	-rm -rf dist
	-rm -rf build

docs: documentation.pdf
	@true

.PHONY = all clean docs

documentation.pdf:
	$(MAKE) -C ./docs latexpdf
	cp ./docs/_build/latex/*.pdf $@
