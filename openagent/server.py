"""
MCP Server — Phase 4.

Optional. Requires: pip install openagent-directive[mcp]

Exposes OpenAgent's analyze pipeline as MCP tools for use
with Claude Desktop and other MCP clients.
"""

try:
    import fastmcp  # noqa: F401
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


def main():
    """Entry point for MCP server. Requires [mcp] extra."""
    if not _MCP_AVAILABLE:
        raise ImportError(
            "MCP server requires the [mcp] extra.\n"
            "Install with: pip install openagent-directive[mcp]"
        )
    raise NotImplementedError("MCP server not yet implemented — Phase 4.")
