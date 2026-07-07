setup:
	uv sync
	uv sync --group dev
	cp .env.example .env
	docker run -d -p 6379:6379 redis
	uv run uvicorn app.main:app --reload

run:
	uv run uvicorn app.main:app --reload

format:
	uv run ruff format . && uv run black .

check:
	uv run ruff check

