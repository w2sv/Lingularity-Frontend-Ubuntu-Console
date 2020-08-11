SHELL=/bin/bash

test:
	mypy lingularity/
	python -m pytest tests/

install-console-env:
	rm -rf console-env
	cat base-environment.yml <(echo) ./lingularity/frontend/console/environment-extension.yml > console-environment.yml
	conda env create -f console-environment.yml --prefix ./console-env
	rm console-environment.yml
	./lingularity/frontend/console/install_dependencies.sh

install-webpage-env:
	rm -rf webpage-env
	cat base-environment.yml <(echo) ./lingularity/frontend/webpage/environment-extension.yml > webpage-environment.yml
	conda env create -f webpage-environment.yml --prefix ./webpage-env
	rm webpage-environment.yml

