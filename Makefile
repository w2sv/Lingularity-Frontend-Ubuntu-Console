SHELL=/bin/bash

# ----------Testing----------

mypy:
	mypy lingularity/

pytest:
	python -m pytest -vv tests/

test: mypy pytest

# ----------Installation--------------

_install-base-dependencies:
	bash os_dependencies/base.sh

install-console-env: _install-base-dependencies
	rm -rf console-env
	cat base-environment.yml <(echo) ./lingularity/frontend/console/environment-extension.yml > console-environment.yml
	conda env create -f console-environment.yml --prefix ./console-env
	rm console-environment.yml
	bash ./lingularity/frontend/console/install-dependencies.sh

install-webpage-env: _install-base-dependencies
	rm -rf webpage-env
	cat base-environment.yml <(echo) ./lingularity/frontend/webpage/environment-extension.yml > webpage-environment.yml
	conda env create -f webpage-environment.yml --prefix ./webpage-env
	rm webpage-environment.yml

