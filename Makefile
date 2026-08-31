.PHONY: test lint run install

install:
	pip install -r requirements-dev.txt

test:
	@python -m pytest --cov=src --cov-report=term-missing --cov-report=xml -q && python -c "from pathlib import Path; p = Path('.git') / 'sdlc-test-run'; p.parent.mkdir(parents=True, exist_ok=True); p.touch()"
	@echo "（已记录：本次会话跑过测试 —— 供 Stop hook 校验）"

lint:
	@command -v ruff >/dev/null 2>&1 || { \
		echo "未找到 ruff，请先执行: make install"; exit 1; }
	ruff check .

run:
	python -m src.api
