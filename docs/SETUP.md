# IBKR TWS MCP Server Setup Guide

This guide provides instructions for setting up and running the IBKR TWS MCP Server for both local development and containerized deployment. The server uses the Model Context Protocol (MCP) with HTTP streaming via chunked transfer encoding for real-time data delivery.

## 1. Prerequisites

Before starting, ensure you have the following installed:

*   **Python 3.11+**
*   **uv** (recommended package installer and project manager)
*   **Docker** and **Docker Compose** (for containerized deployment)
*   **Interactive Brokers Trader Workstation (TWS)** or **IB Gateway** running and logged in. It is highly recommended to use a **Paper Trading** account for all testing.

## 2. Local Development Setup

1.  **Clone the Repository and Navigate:**

    ```bash
    git clone <repository-url>
    cd ibkr-tws-mcp-server
    ```

2.  **Install Dependencies:**

    The project uses `uv` for dependency management.

    ```bash
    uv sync
    ```

3.  **Configure Environment Variables:**

    Create a `.env` file by copying the example and filling in your TWS connection details.

    ```bash
    cp .env.example .env
    # Edit the .env file with your TWS host and port
    ```

    **Example `.env`:**

    ```bash
    # TWS/IB Gateway Connection
    TWS_HOST=127.0.0.1
    TWS_PORT=7497  # 7497 for TWS, 4001 for IB Gateway Paper, 4002 for IB Gateway Live
    TWS_CLIENT_ID=1

    # Server Configuration
    SERVER_HOST=0.0.0.0
    SERVER_PORT=8000
    API_PREFIX=/api/v1
    ```

4.  **Run the Server:**

    The server is an ASGI application run with `uvicorn`.

    ```bash
    uv run python main.py
    # or
    uv run uvicorn src.server:app --host 0.0.0.0 --port 8000
    ```

    The server will be accessible at `http://localhost:8000/api/v1`.

## 3. Containerized Deployment with Docker

1.  **Build the Docker Image:**

    Ensure your `.env` file is configured correctly.

    ```bash
    docker-compose build
    ```

2.  **Run the Container:**

    The `docker-compose.yml` file is configured to use `host.docker.internal` to connect to the TWS/IB Gateway running on your host machine.

    ```bash
    docker-compose up -d
    ```

3.  **Verify Deployment:**

    The server will be running on port `8000` of your host machine.

    ```bash
    curl http://localhost:8000/health
    ```

    You should receive a health check response confirming the server is running.

## 4. Testing

The project includes unit and integration tests.

1.  **Run Unit Tests:**

    ```bash
    uv run pytest tests/unit/
    ```

2.  **Run Integration Tests:**

    **Note:** Integration tests require a running TWS/IB Gateway connected to a paper trading account.

    ```bash
    uv run pytest tests/integration/
    ```

3.  **Run cURL Test Script:**

    This script provides a quick end-to-end check of the server's HTTP interface.

    ```bash
    ./scripts/test_curl.sh
    ```

## 5. Connecting from Claude MCP Inspector

The Claude MCP Inspector is a web-based tool for testing and interacting with MCP servers. You can use it to explore the available tools and test the server's functionality.

### Prerequisites

*   The IBKR TWS MCP server must be running (locally or in Docker)
*   For remote access, you'll need to expose your local server using a tunneling service like **ngrok** or **localtunnel**

### Step-by-Step Guide

1.  **Start the MCP Server**

    Run the server locally:

    ```bash
    uv run python main.py
    ```

    The server will start at `http://localhost:8000/api/v1`.

2.  **Expose the Server (for Remote Access)**

    If you want to connect from the web-based Claude MCP Inspector, you need to expose your local server:

    **Using ngrok:**

    ```bash
    # Install ngrok from https://ngrok.com/download
    ngrok http 8000
    ```

    This will provide a public URL like: `https://xxxx-xxxx-xxxx.ngrok-free.app`

    **Using localtunnel:**

    ```bash
    # Install localtunnel
    npm install -g localtunnel

    # Expose port 8000
    lt --port 8000
    ```

    This will provide a public URL like: `https://your-subdomain.loca.lt`

3.  **Open the Claude MCP Inspector**

    Navigate to: **[https://www.claudemcp.com/inspector](https://www.claudemcp.com/inspector)**

4.  **Configure the Server Connection**

    In the Inspector interface:

    *   Locate the **"Server URL"** or **"Server Endpoint"** input field
    *   Enter your server URL:
        *   **For ngrok:** `https://xxxx-xxxx-xxxx.ngrok-free.app/api/v1/mcp`
        *   **For localtunnel:** `https://your-subdomain.loca.lt/api/v1/mcp`
        *   **For local (advanced):** `http://localhost:8000/api/v1/mcp`
    *   Click **"Connect"**

5.  **Explore and Test Tools**

    Once connected, the Inspector will:
    *   Display all available MCP tools in the sidebar
    *   Show tool descriptions and parameters
    *   Allow you to invoke tools with custom arguments
    *   Display responses and streaming data

6.  **Test the E2E Workflow**

    Try testing the portfolio rebalancing workflow:

    a. **Connect to TWS:**
    *   Select the `ibkr_connect` tool
    *   Enter TWS connection parameters (host, port, clientId)
    *   Click "Invoke"

    b. **Get Market Data:**
    *   Select `ibkr_get_historical_data`
    *   Enter symbol (e.g., "VTI")
    *   Click "Invoke"

    c. **Get Portfolio Data:**
    *   Select `ibkr_get_positions`
    *   Click "Invoke"
    *   Select `ibkr_get_account_summary`
    *   Click "Invoke"

    d. **Place Test Order:**
    *   Select `ibkr_place_order`
    *   Enter order details (symbol, action, quantity)
    *   Click "Invoke"

    e. **Monitor Orders:**
    *   Select `ibkr_get_open_orders`
    *   Click "Invoke"

### Tips for Using the Inspector

*   **Streaming Tools:** Tools like `ibkr_stream_market_data` will show real-time updates in the Inspector's output panel via HTTP streaming with chunked transfer encoding

### Troubleshooting Inspector Connections

* If the Inspector cannot fetch the manifest, try these quick checks:
    - Confirm the server is running: `uv run python main.py`.
    - Try fetching the manifest or health check directly with curl:

```bash
curl -sS http://localhost:8000/health || curl -sS http://localhost:8000/api/v1/mcp
```

* If you see `Task group is not initialized` in server logs, restart the server and ensure you're starting it with the main entrypoint (`uv run python main.py`) so FastMCP can initialize its task groups.

* If the Inspector shows tools but streaming tools are silent, make sure you first call `ibkr_connect` to establish a live TWS connection.

* For remote Inspector sessions (Inspector not running on the same machine), use ngrok/localtunnel to expose your local server and provide the public URL to the Inspector.
*   **Error Messages:** Check the Inspector's console for detailed error messages if a tool fails
*   **Session Management:** The Inspector maintains session state, so you only need to connect to TWS once
*   **CORS Issues:** If you encounter CORS errors when connecting from the web-based Inspector, ensure the server has proper CORS configuration (already included in this implementation)

### Troubleshooting Inspector Connection

| Issue | Solution |
| :--- | :--- |
| **Connection timeout** | Ensure the server is running and accessible at the specified URL. Check firewall settings. |
| **CORS errors** | The server includes CORS middleware. If issues persist, check browser console for specific CORS policy violations. |
| **ngrok/localtunnel errors** | Ensure the tunneling service is running and the URL is correct. Note that free ngrok URLs may have request limits. |
| **404 errors** | Verify you're using the correct endpoint path: `/api/v1/mcp` (not just `/api/v1`) |

## 6. Troubleshooting

| Issue | Potential Cause | Solution |
| :--- | :--- | :--- |
| `ConnectionRefusedError` | TWS/IB Gateway is not running, or the port is incorrect. | Ensure TWS/IB Gateway is running and logged in. Verify `TWS_PORT` in `.env` is correct (e.g., 7497, 4001). |
| `ib_async` timeout | TWS/IB Gateway is running but the connection is blocked. | Check firewall settings. Ensure the host and client ID are correct. |
| Docker connection issue | `host.docker.internal` not resolving. | Ensure your Docker version supports `host-gateway`. Try replacing `host.docker.internal` with your host machine's IP address in the `.env` file. |
