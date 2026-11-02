.PHONY: install run test register clean

install:
	pip install -r requirements.txt

run:
	python main.py

test:
	pytest tests/ -v

register:
	@echo "Paste into Antigravity -> Settings -> MCP -> Add Server:"
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "gemini-gateway": {'
	@echo '      "command": "python",'
	@echo '      "args": ["$(PWD)/mcp/mcp_server.py"],'
	@echo '      "env": {'
	@echo '        "PROXY_URL": "http://localhost:3000",'
	@echo '        "PROXY_API_KEY": "your-gateway-key"'
	@echo '      }'
	@echo '    }'
	@echo '  }'
	@echo '}'

clean:
	find . -name __pycache__ -type d | xargs rm -rf
	rm -rf .pytest_cache
