# NSSM Setup — OpenAgentMCP on Nitro

Runs OpenAgentMCP as a persistent SSE service on port 8008.
TOBOR and other local services connect via http://localhost:8008/sse.

## Prerequisites
- uv installed at C:\Users\cheat\.local\bin\uv.exe
- .env file at C:\Github\OpenAgentMCP\.env with OPENROUTER_API_KEY and OPENAGENT_BASE_URL
- nssm available in PATH

## Install

```powershell
nssm install OpenAgentMCP "C:\Users\cheat\.local\bin\uv.exe"
nssm set OpenAgentMCP AppParameters "run --project C:\Github\OpenAgentMCP openagent serve --transport sse --port 8008"
nssm set OpenAgentMCP AppDirectory C:\Github\OpenAgentMCP
nssm set OpenAgentMCP AppStdout C:\Github\OpenAgentMCP\logs\service.log
nssm set OpenAgentMCP AppStderr C:\Github\OpenAgentMCP\logs\service.log
nssm set OpenAgentMCP AppRotateFiles 1
nssm start OpenAgentMCP
```

## Verify

```powershell
nssm status OpenAgentMCP   # should show SERVICE_RUNNING
curl http://localhost:8008  # should return FastMCP response
```

## Connect from TOBOR / other services

Use mcp-remote or direct SSE client pointed at:
http://localhost:8008/sse

## Claude Desktop (stdio — separate from NSSM)

Claude Desktop uses stdio transport, not the NSSM SSE service.
Add to claude_desktop_config.json:
```json
{
  "openagent": {
    "command": "uv",
    "args": ["run", "--with", "openagent-directive[mcp]", "openagent", "serve"],
    "cwd": "C:\\Github\\OpenAgentMCP"
  }
}
```

## Restart after code changes

```powershell
nssm restart OpenAgentMCP
```
