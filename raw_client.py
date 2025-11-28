import subprocess
import sys
import json
import time

def run():
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=0
    )

    # 1. Send Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    print(f"Sending: {json.dumps(init_req)}")
    process.stdin.write(json.dumps(init_req) + "\n")
    process.stdin.flush()

    # Read response
    response = process.stdout.readline()
    print(f"Received: {response}")

    # 2. Send Initialized
    init_notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    print(f"Sending: {json.dumps(init_notif)}")
    process.stdin.write(json.dumps(init_notif) + "\n")
    process.stdin.flush()

    # 3. Send List Tools
    list_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    print(f"Sending: {json.dumps(list_req)}")
    process.stdin.write(json.dumps(list_req) + "\n")
    process.stdin.flush()

    # Read response
    response = process.stdout.readline()
    print(f"Received: {response}")

    # 4. Call get_provider_data
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_provider_data",
            "arguments": {"npi": 1003000126}
        }
    }
    print(f"Sending: {json.dumps(call_req)}")
    process.stdin.write(json.dumps(call_req) + "\n")
    process.stdin.flush()

    # Read response
    response = process.stdout.readline()
    print(f"Received: {response}")

    process.terminate()

if __name__ == "__main__":
    run()
