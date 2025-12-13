# Testing MCP Server Features

This guide explains how to interact with and test the Multi-Agent Coordination Protocol (MCP) server (`mcp_server.py`).

## 1. Prerequisites
Ensure the MCP server is running:
```bash
python mcp_server.py
```
*The server runs on `stdio` by default, but for testing purposes, we can simulate interactions or use an MCP inspector if available. Since this implementation uses `mcp.server.fastmcp`, it might also expose a local server if configured.*

**Note:** The current `mcp_server.py` is configured to run over stdio (standard input/output) for integration with MCP clients (like Claude Desktop or other agents). To test it manually, you can write a simple Python client script.

## 2. Testing with a Python Client Script
Create a file named `test_mcp.py` to interact with the server programmatically.

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. List Tools
            print("--- Tools ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # 2. List Resources
            print("\n--- Resources ---")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"- {resource.uri}: {resource.name}")

            # 3. Call a Tool (e.g., predict_fraud_risk)
            print("\n--- Testing Tool: predict_fraud_risk ---")
            # Replace with a valid NPI from your dataset
            npi = 1003000126 
            result = await session.call_tool("predict_fraud_risk", arguments={"npi": npi})
            print(f"Risk Score for {npi}: {result.content[0].text}")

            # 4. Read a Resource (e.g., High Risk List)
            print("\n--- Reading Resource: fraud://providers/list ---")
            res_content = await session.read_resource("fraud://providers/list")
            print(res_content.contents[0].text[:500] + "...") # Print first 500 chars

if __name__ == "__main__":
    asyncio.run(run())
```

## 3. Manual Testing (via Curl/API)
If the MCP server were running over HTTP (SSE), you could use `curl`. However, since it's running over stdio, the Python script above is the best way to verify functionality.

## 4. Key Features to Verify

### Tools
*   `get_provider_data(npi)`: Should return a JSON string of raw features.
*   `predict_fraud_risk(npi)`: Should return a float between 0.0 and 1.0.
*   `explain_fraud_risk(npi)`: Should return a text description of SHAP values.

### Resources
*   `fraud://providers/list`: Should return a Markdown table of high-risk providers.
*   `fraud://providers/{npi}`: Should return a detailed Markdown report for a specific provider.

## 5. Troubleshooting
*   **Server not starting**: Check if `uvicorn` or other processes are blocking ports (though stdio shouldn't have port conflicts).
*   **"Provider not found"**: Ensure you are using an NPI that exists in the `feature_store` (check `data/` directory or the dashboard).
