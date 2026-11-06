"""Publisher MCP Server entry point."""

import sys
from mcp.server.mcpserver import MCPServer

# Initialize MCP server
mcp = MCPServer(
    name="ai-publisher",
    instructions="MCP server providing persistent state, validation, and gated publishing for AI Publisher.",
)


@mcp.tool()
def ping() -> str:
    """Check health and connectivity of the AI Publisher MCP server."""
    return "pong"


@mcp.tool()
def get_system_status() -> dict:
    """Return runtime environment status and database connectivity info."""
    return {
        "status": "online",
        "service": "ai-publisher-mcp",
        "version": "0.1.0",
        "python_version": sys.version,
    }


def main():
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
