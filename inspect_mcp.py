import mcp
import mcp.server
print(dir(mcp.server))
try:
    from mcp.server import Server
    print("Server found in mcp.server")
except ImportError:
    print("Server NOT found in mcp.server")

try:
    from mcp.server.lowlevel import Server
    print("Server found in mcp.server.lowlevel")
except ImportError:
    print("Server NOT found in mcp.server.lowlevel")
