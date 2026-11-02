.PHONY: install run test register cookie clean

install:
	pip install -r requirements.txt
	playwright install chromium

run:
	python main.py

test:
	pytest tests/ -v

cookie:
	python scripts/get_cookie.py

register:
	@echo "Paste into Antigravity -> Settings -> MCP -> Add Server:"
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "chatgpt-proxy": {'
	@echo '      "command": "python",'
	@echo '      "args": ["$(PWD)/mcp/mcp_server.py"],'
	@echo '      "env": {'
	@echo '        "PROXY_URL": "http://localhost:3000",'
	@echo '        "PROXY_API_KEY": "your-key"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo '}'

clean:
	find . -name __pycache__ -type d | xargs rm -rf
	rm -rf .pytest_cache
