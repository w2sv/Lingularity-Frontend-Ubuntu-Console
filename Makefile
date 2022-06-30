SHELL=/bin/bash

# ----------Installation--------------

install:
	chmod +x ./install-linux-dependencies
	./install-linux-dependencies.sh

	rm -rf env
	mamba env create -f environment.yml --prefix ./env

reinstall-backend:
	chmod +x ./build-and-reinstall-backend.sh
	./build-and-reinstall-backend.sh

# ----------Testing----------

test: mypy pytest doctest  # run with -k flag in order to continue in case of recipe failure

mypy:
	mypy frontend/src/

pytest:
	coverage run -m pytest -vv tests/

doctest:
	python -m pytest -vv --doctest-modules --doctest-continue-on-failure ./frontend/src/
