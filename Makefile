PYTHON ?= python3

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

test:
	$(PYTHON) -m unittest discover -s Tests -t . -v

lint:
	$(PYTHON) -m ruff check $(ROOT_DIR)
	$(PYTHON) -m ruff format --check $(ROOT_DIR)

reformat:
	$(PYTHON) -m ruff check --fix $(ROOT_DIR)
	$(PYTHON) -m ruff format $(ROOT_DIR)

install:
	pip install -U -r requirements.txt

install-dev:
	pip install -U -r requirements-dev.txt
