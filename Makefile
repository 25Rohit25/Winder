.PHONY: help install test lint generate-data validate report run docker-up docker-down demo clean

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
NPM ?= npm

help:
	@echo "WindCtrl Validate - Automated Turbine Controller Toolkit"
	@echo ""
	@echo "Targets:"
	@echo "  make install        Install backend and frontend dependencies"
	@echo "  make test           Execute full pytest suite (unit, property, integration, regression)"
	@echo "  make lint           Run code formatting and style linters"
	@echo "  make generate-data  Synthesize NREL 5MW turbine telemetry datasets"
	@echo "  make validate       Execute automated controller validation checks"
	@echo "  make report         Compile certification PDF and LaTeX reports"
	@echo "  make run            Start local FastAPI backend server"
	@echo "  make docker-up      Launch full platform via Docker Compose"
	@echo "  make docker-down    Stop Docker Compose containers"
	@echo "  make demo           One-shot end-to-end demo execution"
	@echo "  make clean          Remove transient test caches and build artifacts"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	cd frontend && $(NPM) install

test:
	$(PYTHON) -m pytest backend/tests/ -v

lint:
	$(PIP) install ruff
	ruff check backend/ scripts/

generate-data:
	$(PYTHON) scripts/generate_sample_data.py

validate:
	$(PYTHON) scripts/run_validation.py --all-baseline

report:
	$(PYTHON) scripts/generate_report.py data/baseline/normal_run.csv

run:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

video-start:
	cd video && $(NPM) start

video-render:
	cd video && $(NPM) run render

demo: generate-data validate report
	@echo ""
	@echo "================================================================="
	@echo " WindCtrl Validate Demo Complete!"
	@echo " 1. Synthetic datasets created in: data/"
	@echo " 2. Validation results verified."
	@echo " 3. Multi-channel telemetry plots generated."
	@echo " 4. LaTeX source & Audit PDF generated in: reports/generated/"
	@echo "================================================================="

clean:
	rm -rf .pytest_cache htmlcov .coverage frontend/dist reports/generated/*/*.aux reports/generated/*/*.log
