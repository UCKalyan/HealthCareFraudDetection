import sys
import json
import subprocess
import time

def run_test():
    print("--- Starting MCP Server Test ---")
    
    # Start the server process
    stderr_file = open("server_stderr.log", "w")
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=stderr_file,
        text=True,
        bufsize=0
    )

    try:
        # Helper to send/receive
        def send_request(method, params=None, req_id=None):
            req = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {}
            }
            if req_id is not None:
                req["id"] = req_id
            
            json_req = json.dumps(req)
            # print(f"Sending: {json_req}")
            process.stdin.write(json_req + "\n")
            process.stdin.flush()
            
            if req_id is not None:
                response = process.stdout.readline()
                print(f"DEBUG Received: {response.strip()}")
                if not response:
                    print(f"DEBUG: Empty response. Process poll: {process.poll()}")
                    return {}
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    print("FAILED TO PARSE JSON")
                    return {}
            return None

        # 1. Initialize
        print("\n1. Initializing...")
        init_res = send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }, req_id=1)
        print("   Server Info:", init_res["result"]["serverInfo"])

        # 2. Initialized Notification
        send_request("notifications/initialized")

        # 3. List Tools
        print("\n2. Listing Tools...")
        tools_res = send_request("tools/list", req_id=2)
        tools = tools_res["result"]["tools"]
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description'].strip().splitlines()[0]}")

        # 4. Call Tool: predict_fraud_risk
        npi = 1003000126
        print(f"\n3. Calling Tool: predict_fraud_risk (NPI: {npi})...")
        pred_res = send_request("tools/call", {
            "name": "predict_fraud_risk",
            "arguments": {"npi": npi}
        }, req_id=3)
        
        if "error" in pred_res:
            print("   Error:", pred_res["error"])
        else:
            content = pred_res["result"]["content"][0]["text"]
            print(f"   Risk Score: {content}")

        # 5. Call Tool: explain_fraud_risk
        print(f"\n4. Calling Tool: explain_fraud_risk (NPI: {npi})...")
        expl_res = send_request("tools/call", {
            "name": "explain_fraud_risk",
            "arguments": {"npi": npi}
        }, req_id=4)
        
        if "error" in expl_res:
            print("   Error:", expl_res["error"])
        else:
            content = expl_res["result"]["content"][0]["text"]
            print("   Explanation:")
            for line in content.splitlines():
                print(f"     {line}")

        # 6. List Resources
        print("\n5. Listing Resources...")
        # Note: FastMCP might not implement resources/list if not explicitly added, 
        # but we added @mcp.resource so it should be there.
        # However, the raw client output didn't show resources capability in initialize result?
        # Wait, initialize result showed: "resources": {"subscribe": false, "listChanged": false}
        # So it supports resources.
        res_list = send_request("resources/list", req_id=5)
        if "error" in res_list:
             print("   Error listing resources:", res_list["error"])
        else:
             resources = res_list["result"].get("resources", [])
             for res in resources:
                 print(f"   - {res['uri']}: {res['name']}")

        # 7. Read Resource
        print("\n6. Reading Resource: fraud://providers/list")
        read_res = send_request("resources/read", {
            "uri": "fraud://providers/list"
        }, req_id=6)
        
        if "error" in read_res:
            print("   Error reading resource:", read_res["error"])
        else:
            content = read_res["result"]["contents"][0]["text"]
            print("   Content Preview:")
            print(content[:200] + "...")

    except Exception as e:
        print(f"\nTest Failed: {e}")
    finally:
        process.terminate()
        print("\n--- Test Complete ---")

if __name__ == "__main__":
    run_test()