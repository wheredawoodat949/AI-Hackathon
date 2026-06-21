# Rapid dev commands. Override the match with: make frame MATCH=118575
MATCH ?= 117093
PY ?= python

.PHONY: setup test lint gpu download download-video frame clean help

help:
	@echo "make setup          # venv + editable install (.venv, dev extras)"
	@echo "make test           # run the pytest suite (no GPU/data needed)"
	@echo "make lint           # ruff check"
	@echo "make gpu            # CUDA check (fails loud if no GPU)"
	@echo "make download       # Drive mirror, annotations only (MATCH=$(MATCH))"
	@echo "make download-video # Drive mirror, annotations + panorama video"
	@echo "make frame          # print one real GSR frame (MATCH=$(MATCH))"

setup:
	$(PY) -m venv .venv
	./.venv/bin/pip install -U pip
	./.venv/bin/pip install -e ".[dev]"
	@echo "Activate with: source .venv/bin/activate"

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests

gpu:
	$(PY) -m src.utils.gpu

download:
	$(PY) -m src.data.download --match $(MATCH) --no-videos

download-video:
	$(PY) -m src.data.download --match $(MATCH)

frame:
	$(PY) -m src.data.inspect --match $(MATCH)

clean:
	rm -rf .pytest_cache **/__pycache__ src/**/__pycache__
