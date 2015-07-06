
clean:
	@echo ""
	@echo "Clean the python virtualenv, distribution and package folders/files."
	rm -rf build dist po terra.egg-info

	@echo ""
	@echo "Clean the byte-compiled, optimized or DLL files."
	find . -name __pycache__ | xargs -i rm -rf {}
	find . -name '*.py[cod]' | xargs -i rm -rf {}
	@echo ""

TERRA_VERSION=$(shell grep '__version__' terra/__init__.py | cut -d\' -f2)
XGETTEXT_ARGS= --add-comments --indent --no-wrap --package-name=terra --package-version=$(TERRA_VERSION) --default-domain=terra --output-dir=locales
i18n-extract:
	@mkdir -p locales
	@echo "Extracting strings..."
	@xgettext $(XGETTEXT_ARGS) --language=python --keyword=t terra/*.py
	@xgettext $(XGETTEXT_ARGS) --join-existing --language=python --keyword=t terra/handlers/*.py
	@xgettext $(XGETTEXT_ARGS) --join-existing --language=python --keyword=t terra/interfaces/*.py
	@xgettext $(XGETTEXT_ARGS) --join-existing --language=glade terra/resources/*.ui
	@echo "Done!"
