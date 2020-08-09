SHELL=/bin/bash

test:
	mypy lingularity/
	python -m pytest tests/

install-terminal-env:
	rm -rf terminal-env
	conda env create -f base-environment.yml --prefix ./terminal-env
	conda env update --prefix ./terminal-env --file lingularity/frontend/terminal/dependencies.yml

install-webpage-env:
	rm -rf webpage-env
	conda env create -f base-environment.yml --prefix ./webpage-env
	conda env update --prefix ./terminal-env --file lingularity/frontend/webpage/dependencies.yml
