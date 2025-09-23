# N8n MCP Integration Update

## Overview

The production module has been **fully migrated** to use an external n8n MCP server hosted on Railway using the `ghcr.io/czlonkowski/n8n-mcp-railway:latest` container. The bot no longer needs a direct connection to n8n - everything goes through the MCP server.

## Architecture

```
UMBRA Bot → N8n MCP Server (Railway) → Your N8n Instance
```

**Benefits:**
- **Single Point of Connection**: MCP server handles all n8n communication
- **Protocol Standardization**: Uses MCP for consistent tool communication  
- **Simplified Configuration**: No need for direct n8n credentials in bot
- **Better Security**: MCP server acts as secure proxy
- **Railway Optimized**: Designed specifically for Railway deployment

## Changes Made

### 1. Complete MCP Migration

**Removed Direct n8n Client**: The production module no longer uses direct n8n REST API calls. All communication flows through the MCP server:

- **New MCP Client** (`n8n_mcp_client.py`): Communicates exclusively with MCP server
- **Updated Components**: All production components now use MCP client only
- **Simplified Architecture**: Single communication path to n8n via MCP

### 2. Updated Production Module

Modified `production_mcp.py` and all components:
- Removed `N8nClient` dependencies
- Updated all components to use `N8nMCPClient` exclusively
- Maintained all existing functionality through MCP protocol

### 3. Simplified Configuration

**Primary Configuration** (MCP Server):
```bash
# N8n MCP Server Configuration (RECOMMENDED)
N8N_MCP_SERVER_URL=https://your-n8n-mcp.railway.app
N8N_MCP_API_KEY=your_mcp_api_key
```

**Legacy Support** (Optional fallback):
```bash
# Direct n8n connection (fallback only)
MAIN_N8N_URL=https://your-n8n.railway.app
```

### 4. Enhanced Security & Reliability

- **No Direct Credentials**: Bot doesn't need direct n8n API access
- **MCP Proxy**: MCP server handles all authentication with n8n
- **Single Point of Failure**: Only MCP server needs n8n access
- **Better Error Handling**: MCP protocol provides standardized error responses

## MCP Server Setup

To use this integration:

1. **Deploy the MCP Server**: Use the Railway container `ghcr.io/czlonkowski/n8n-mcp-railway:latest`

2. **Configure Environment Variables**:
   ```bash
   N8N_MCP_SERVER_URL=https://your-n8n-mcp.railway.app
   N8N_MCP_API_KEY=your_api_key  # If required by your MCP server
   ```

3. **Connect to Your N8n Instance**: The MCP server should be configured to connect to your main n8n instance

## Benefits

- **Protocol Standardization**: Uses MCP for consistent tool communication
- **Better Error Handling**: Enhanced error reporting through MCP protocol
- **Railway Optimized**: Designed specifically for Railway deployment
- **Future-Proof**: Easily extensible for additional MCP tools
- **Backward Compatible**: Fallback to direct n8n API if needed

## Usage

The production module interface remains the same. All existing commands and workflows continue to work:

```python
# List workflows
await production_module.execute("list_workflows", {})

# Create workflow
await production_module.execute("create_workflow", {"workflow": workflow_data})

# Run workflow
await production_module.execute("run_workflow", {"id": workflow_id, "payload": data})
```

The MCP integration is transparent to the end user while providing enhanced functionality under the hood.