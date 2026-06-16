install:
	bash scripts/install.sh

run:
	bash scripts/run.sh

health:
	bash scripts/healthcheck.sh

test:
	./venv/bin/pytest -q
