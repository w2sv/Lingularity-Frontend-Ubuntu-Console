SHELL=/bin/bash

test:
	mypy src/
	python -m pytest tests/