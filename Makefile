SHELL=/bin/bash

# ----------Installation--------------

install:
	bash os-dependencies/backend.sh
	bash os-dependencies/frontend.sh

	rm -rf env
	conda env create -f environment.yml --prefix ./env

# ----------Testing----------

test: mypy pytest doctest  # run with -k flag in order to continue in case of recipe failure

mypy:
	mypy lingularity/

pytest:
	coverage run -m pytest -vv tests/

doctest:
	python -m pytest -vv --doctest-modules --doctest-continue-on-failure ./lingularity/

# ----------Mining--------------

mine-metadata:
	python -m lingularity.backend.metadata.mine -Mine
