SHELL=/bin/bash

test:
	mypy lingularity/
	python -m pytest tests/

install:
	rm -rf env
	conda env create -f environment.yml --prefix ./env