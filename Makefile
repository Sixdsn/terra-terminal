
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
i18n-extract:
	@mkdir -p locales
	@rm -rf locales/messages.po
	@echo "Extracting strings..."
	@xgettext --keyword=t --add-comments --package-name=terra \
		--output-dir=locales --language=python \
		--package-version=$(TERRA_VERSION) terra/*.py
	@echo "Done!"
