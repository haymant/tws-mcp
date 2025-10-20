# Project Structure

This document describes the organization of the IBKR TWS MCP Server project.

## Root Directory

```
ibkr-tws-mcp-server/
├── main.py                 # Application entry point
├── pyproject.toml          # Project dependencies and configuration
├── uv.lock                 # Locked dependency versions
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment configuration
├── README.md               # Project overview and quick start
├── Dockerfile              # Docker container configuration
├── docker-compose.yml      # Docker Compose setup
└── .gitignore              # Git ignore patterns
```

## Source Code (`src/`)

```
src/
├── __init__.py             # Package initialization
├── server.py               # FastMCP server and tool definitions
├── tws_client.py           # TWS/IB Gateway client wrapper
└── models.py               # Pydantic data models
```

## Tests (`tests/`)

```
tests/
├── unit/                   # Unit tests with mocks
│   ├── __init__.py
│   ├── test_tws_client.py  # TWSClient unit tests
│   └── test_server_tools.py # Server tools unit tests
├── integration/            # Integration tests (manual)
│   ├── __init__.py
│   ├── README.md           # Integration testing guide
│   └── test_e2e_workflow.py # E2E workflow documentation
└── fixtures/               # Test data fixtures
    └── sample_positions.json
```

## Documentation (`docs/`)

```
docs/
├── API.md                              # MCP tools API reference
├── Design.md                           # Architecture and design
├── SETUP.md                            # Setup and deployment guide
├── MIGRATION_TO_IB_ASYNC.md           # ib-insync → ib_async migration
├── CANCELLEDERROR_TROUBLESHOOTING.md  # Connection troubleshooting
├── FIX_EVENT_LOOP_ALREADY_RUNNING.md  # Event loop fix documentation
├── INTEGRATION_TEST_404_EXPLAINED.md  # MCP vs REST explanation
├── TWS_API_HANDSHAKE_TIMEOUT.md       # TWS handshake debugging
├── CURRENT_ISSUE_TWS_API_BLOCKED.md   # Historical issue tracking
├── FIX_SUMMARY.md                      # Summary of fixes applied
├── IB_ASYNC_MIGRATION_COMPLETE.md     # Migration completion status
└── IMPLEMENTATION_STATUS.md            # Implementation checklist
```

## Scripts (`scripts/`)

```
scripts/
└── test_curl.sh            # cURL-based API testing script
```

## Diagnostic Tools (`diagnostics/`)

Development and troubleshooting scripts:

```
diagnostics/
├── README.md                   # Diagnostic tools guide
├── test_tws_connection.py      # TWS connection diagnostic
├── test_minimal_tws.py         # Minimal connection test
├── check_ib_loop_attrs.py      # IB loop attributes inspector
├── check_ib_client_loop.py     # IB client loop checker
├── inspect_ib_structure.py     # IB structure inspector
├── verify_loop_fix.py          # Event loop fix verification
├── test_fastmcp_methods.py     # FastMCP methods inspector
├── test_mcp_http_app.py        # MCP HTTP app inspector
├── test_sse_app.py             # SSE app inspector
├── test_server_endpoints.py    # Endpoint availability test
├── quick_test.py               # Quick server test
├── runtime_check.py            # Runtime verification
├── test_runtime_quick.py       # Quick runtime test
├── final_test.py               # Final verification
└── verify_setup.py             # Setup verification
```

## VS Code Configuration (`.vscode/`)

```
.vscode/
└── launch.json             # Debug configurations for VS Code
```

## Development Workflow

### Running Tests
```bash
# Unit tests
uv run pytest tests/unit/ -v

# Specific test file
uv run pytest tests/unit/test_tws_client.py -v

# Integration tests (manual)
# See tests/integration/README.md
```

### Running Diagnostics
```bash
# Test TWS connection
uv run python diagnostics/test_tws_connection.py --port 7497

# Quick server check
uv run python diagnostics/quick_test.py
```

### Running the Server
```bash
# Development
uv run python main.py

# Production (Docker)
docker-compose up
```

## File Naming Conventions

- **`*_test.py`** → Unit tests in `tests/unit/`
- **`test_*.py`** → Diagnostic scripts in `diagnostics/`
- **`*.md`** → Documentation in `docs/`
- **`*_client.py`** → Client implementations in `src/`
- **`models.py`** → Data models in `src/`
- **`server.py`** → Server/API definitions in `src/`

## Key Files

### Essential for Running
- `main.py` - Start here
- `src/server.py` - MCP tool definitions
- `src/tws_client.py` - TWS integration
- `.env` - Configuration (copy from `.env.example`)

### Essential for Development
- `pyproject.toml` - Dependencies
- `tests/unit/` - Unit tests
- `docs/SETUP.md` - Setup guide
- `docs/API.md` - API reference

### Essential for Deployment
- `Dockerfile` - Container image
- `docker-compose.yml` - Orchestration
- `.env.example` - Config template

## Adding New Features

1. **Add tool logic** → `src/tws_client.py`
2. **Expose as MCP tool** → `src/server.py` (use `@mcp.tool()`)
3. **Add unit tests** → `tests/unit/test_tws_client.py`
4. **Update documentation** → `docs/API.md`
5. **Update README** → Add to feature list

## Getting Help

- **Setup issues** → See `docs/SETUP.md`
- **API reference** → See `docs/API.md`
- **Architecture** → See `docs/Design.md`
- **Connection problems** → See `docs/CANCELLEDERROR_TROUBLESHOOTING.md`
- **Diagnostic tools** → See `diagnostics/README.md`
