SHELL=/bin/bash

# ----------Installation--------------

install:
	bash os-dependencies.sh

	rm -rf env
	conda env create -f environment.yml --prefix ./env

reinstall-backend:
	pip uninstall -y backend
	pip install /home/w2sv/W2SV/python/projects/lingularity/dist/backend-0.1.1-py3-none-any.whl


# ----------Testing----------

test: mypy pytest doctest  # run with -k flag in order to continue in case of recipe failure

mypy:
	mypy frontend/

pytest:
	coverage run -m pytest -vv tests/

doctest:
	python -m pytest -vv --doctest-modules --doctest-continue-on-failure ./lingularity/

# ----------Building-------------

build:
	python -OO -m PyInstaller --noconfirm --clean lingularity/frontend/__init__.py \
 				--name Lingularity \
 				--distpath="./build/dist" \
				--workpath="./build/build" \
				--specpath="./build" \
 				--add-data=".language_data/*:language_data" \
 				--add-data="backend/metadata/data/*:metadata" \
 				--add-data="backend/ops/google/text_to_speech/identifiers.json:text_to_speech_identifiers.json" \
 				--add-data="frontend/banners/*:banners" \
				--exclude-module bs4 \
				--exclude-module coverage \
				--exclude-module pytest \
				--exclude-module mypy \
