PYTHON ?= python3
SOURCE ?= examples/web.conf

.PHONY: run demo test style

run:
	$(PYTHON) -m src.main < "$(SOURCE)"

demo:
	$(PYTHON) -m scripts.demo

test:
	$(PYTHON) -m pytest tests/ -q

style:
	$(PYTHON) -m scripts.check_style
