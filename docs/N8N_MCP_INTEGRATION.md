# N8n MCP Integration Update

## Overview

The production module has been updated to use an external n8n MCP server hosted on Railway using the `ghcr.io/czlonkowski/n8n-mcp-railway:latest` container.

## Changes Made

### 1. New MCP Client (`n8n_mcp_client.py`)

Created a new MCP client that communicates with the external n8n MCP server instead of directly with n8n's REST API. This provides:

- **Better Integration**: Uses the MCP protocol for standardized tool communication
- **Railway Compatibility**: Designed for the czlonkowski/n8n-mcp-railway container
- **Enhanced Features**: Access to MCP-specific n8n operations
- **Same Interface**: Compatible with existing production module components

### 2. Updated Production Module

Modified `production_mcp.py` to use the new MCP client:
- Replaced direct n8n client with MCP client
- Maintained all existing functionality
- Added support for MCP-specific operations

### 3. Configuration Updates

Added new environment variables for MCP server configuration:

```bash
# N8n MCP Server Configuration (Railway-hosted)
N8N_MCP_SERVER_URL=https://your-n8n-mcp.railway.app
N8N_MCP_API_KEY=your_mcp_api_key
N8N_MCP_AUTH_TOKEN=your_mcp_auth_token
```

### 4. Component Compatibility

Updated production components to accept both N8nClient and N8nMCPClient:
- `WorkflowValidator`: Updated type hints for MCP client compatibility
- `CatalogManager`: Compatible with MCP client interface
- `WorkflowExporter`: Works with both client types
- Other components: Use the same interface pattern

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