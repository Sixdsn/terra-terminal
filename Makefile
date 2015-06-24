
clean:
	@echo ""
	@echo "Clean the python virtualenv, distribution and package folders/files."
	rm -rf build dist po terra.egg-info

	@echo ""
	@echo "Clean the byte-compiled, optimized or DLL files."
	find . -name __pycache__ | xargs -i rm -rf {}
	find . -name '*.py[cod]' | xargs -i rm -rf {}
	@echo ""
