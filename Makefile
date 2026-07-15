.PHONY: install test report-dry-run workbench clean

install:
	python -m pip install -e ".[dev,pdf]"

test:
	python -m unittest discover -s tests

report-dry-run:
	python -m crypto_intel.cli daily-report --dry-run --no-email

workbench:
	python -m crypto_intel.cli serve

clean:
	python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['artifacts', 'data/__pycache__']]"
