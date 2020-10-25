SHELL=/bin/bash

# ----------Testing----------

mypy:
	mypy lingularity/

pytest:
	coverage run -m pytest -vv tests/

doctest:
	python -m pytest -vv --doctest-modules --doctest-continue-on-failure ./lingularity/ --ignore ./lingularity/frontend/webpage/

test: mypy pytest doctest  # run with -k flag in order to keep going in case of recipe failure

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

# ----------Mining--------------

mine-metadata:
	python -m lingularity.backend.metadata.mine -Mine
