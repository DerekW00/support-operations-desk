.PHONY: verify test demo browser
verify:
	uv sync --frozen
	uv run python manage.py check
	uv run python manage.py makemigrations --check --dry-run
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy support config manage.py
	uv run pytest --ignore=tests/test_browser.py
	uv run python manage.py evaluate
test:
	uv run pytest
browser:
	uv run pytest tests/test_browser.py -q
demo:
	uv run python manage.py migrate
	uv run python manage.py demo
	uv run python manage.py runserver 127.0.0.1:8101
