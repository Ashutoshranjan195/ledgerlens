.PHONY: setup run eval update test airplane clean

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	ollama pull qwen2.5:7b-vl || true

run:
	. .venv/bin/activate && python -m app.main

eval:
	. .venv/bin/activate && python evals/run.py \
	  --strict \
	  --report evals/reports/$(shell date +%F).json

update:
	. .venv/bin/activate && python -m app.cli update --all

test:
	. .venv/bin/activate && pytest -q

airplane:
	bash scripts/airplane_mode_test.sh

clean:
	rm -rf .venv __pycache__ **/__pycache__ .pytest_cache evals/reports/*
