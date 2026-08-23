.PHONY: build-benchmark validate-annotations run-pilot run-models evaluate tables figures test lint format

build-benchmark:
	python scripts/build_benchmark.py --config configs/benchmark.yaml

validate-annotations:
	python scripts/validate_annotations.py --input data/annotations/privacy_labels.jsonl

run-pilot:
	python scripts/run_pilot.py --config configs/benchmark.yaml --models configs/models.yaml

run-models:
	python scripts/run_models.py --config configs/benchmark.yaml --models configs/models.yaml --output results/raw_generations/

evaluate:
	python scripts/evaluate_results.py --config configs/evaluation.yaml --input results/raw_generations/ --output results/metrics/

tables:
	python scripts/generate_tables.py --input results/metrics/ --output results/tables/

figures:
	python scripts/generate_figures.py --input results/metrics/ --output results/figures/

test:
	pytest

lint:
	ruff check .
	black --check .

format:
	ruff check --fix .
	black .
