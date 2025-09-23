"""
N8n MCP Client for Production Module

Communicates with external n8n MCP server hosted on Railway
using the czlonkowski/n8n-mcp-railway container.
"""

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import aiohttp

from ...core.config import UmbraConfig

logger = logging.getLogger(__name__)

@dataclass
class N8nMCPCredentials:
    """N8n MCP server authentication credentials"""
    api_key: str | None = None
    auth_token: str | None = None
    auth_type: str = "api_key"  # api_key, token, none

class N8nMCPClient:
    """MCP client for external n8n MCP server communication"""

    def __init__(self, config: UmbraConfig):
        self.config = config
        self.server_url = self._resolve_mcp_server_url()
        self.credentials = self._load_credentials()
        self.session = None

        # MCP-specific endpoints
        self.endpoints = {
            "tools": "/mcp/tools",
            "resources": "/mcp/resources",
            "prompts": "/mcp/prompts",
            "execute": "/mcp/execute",
            "health": "/health"
        }

        logger.info(f"N8n MCP client initialized for {self.server_url}")

    def _resolve_mcp_server_url(self) -> str:
        """Resolve n8n MCP server URL"""
        # Use the Railway-hosted MCP server URL
        url = self.config.get("N8N_MCP_SERVER_URL")
        if url:
            return url.rstrip("/")

        # Check for main n8n URL as fallback
        main_url = self.config.get("MAIN_N8N_URL")
        if main_url:
            # If it's a direct n8n instance, assume MCP is on the same domain
            return main_url.rstrip("/")

        # Default Railway MCP server pattern
        # You should set this in your environment
        return "https://your-n8n-mcp.railway.app"

    def _load_credentials(self) -> N8nMCPCredentials:
        """Load n8n MCP server authentication credentials"""
        api_key = self.config.get("N8N_MCP_API_KEY")
        auth_token = self.config.get("N8N_MCP_AUTH_TOKEN")
        
        # Also try standard n8n credentials as fallback
        n8n_api_key = self.config.get("N8N_API_KEY")

        if api_key:
            return N8nMCPCredentials(api_key=api_key, auth_type="api_key")
        elif auth_token:
            return N8nMCPCredentials(auth_token=auth_token, auth_type="token")
        elif n8n_api_key:
            return N8nMCPCredentials(api_key=n8n_api_key, auth_type="api_key")
        else:
            return N8nMCPCredentials(auth_type="none")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with auth"""
        if self.session is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "UMBRA-Production-Module/1.0"
            }

            # Add authentication based on MCP server requirements
            if self.credentials.auth_type == "api_key" and self.credentials.api_key:
                headers["Authorization"] = f"Bearer {self.credentials.api_key}"
            elif self.credentials.auth_type == "token" and self.credentials.auth_token:
                headers["X-MCP-Token"] = self.credentials.auth_token

            timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for workflow operations
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )

        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make authenticated HTTP request to MCP server"""
        session = await self._get_session()
        url = urljoin(self.server_url, endpoint)

        try:
            async with session.request(method, url, **kwargs) as response:
                if response.content_type == "application/json":
                    data = await response.json()
                else:
                    text = await response.text()
                    data = {"text": text}

                if response.status >= 400:
                    error_msg = data.get("error", {}).get("message", f"HTTP {response.status}")
                    raise Exception(f"N8n MCP error: {error_msg}")

                return data

        except aiohttp.ClientError as e:
            logger.error(f"N8n MCP request failed: {e}")
            raise Exception(f"N8n MCP connection error: {e}") from e

    async def health_check(self) -> dict[str, Any]:
        """Check n8n MCP server health"""
        try:
            result = await self._request("GET", self.endpoints["health"])
            return {"status": "healthy", "data": result}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools from n8n server"""
        try:
            result = await self._request("GET", self.endpoints["tools"])
            return result.get("tools", [])
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool via MCP"""
        payload = {
            "name": tool_name,
            "arguments": arguments
        }

        try:
            result = await self._request("POST", self.endpoints["execute"], json=payload)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e), "success": False}

    # Workflow-specific methods using MCP tools

    async def list_workflows(self, query: str | None = None, tag: str | None = None, limit: int = 50) -> dict[str, Any]:
        """List workflows via MCP"""
        arguments = {"limit": limit}
        if query:
            arguments["filter"] = query
        if tag:
            arguments["tags"] = tag

        return await self.execute_tool("list_workflows", arguments)

    async def get_workflow(self, workflow_id: str | None = None, workflow_name: str | None = None) -> dict[str, Any]:
        """Get workflow by ID or name via MCP"""
        arguments = {}
        if workflow_id:
            arguments["id"] = workflow_id
        elif workflow_name:
            arguments["name"] = workflow_name
        else:
            return {"error": "Either workflow_id or workflow_name must be provided"}

        return await self.execute_tool("get_workflow", arguments)

    async def create_workflow(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Create new workflow via MCP"""
        return await self.execute_tool("create_workflow", {"workflow": workflow_data})

    async def update_workflow(self, workflow_id: str, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Update existing workflow via MCP"""
        return await self.execute_tool("update_workflow", {
            "id": workflow_id,
            "workflow": workflow_data
        })

    async def delete_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Delete workflow via MCP"""
        return await self.execute_tool("delete_workflow", {"id": workflow_id})

    async def enable_workflow(self, workflow_id: str, active: bool = True) -> dict[str, Any]:
        """Enable or disable workflow via MCP"""
        return await self.execute_tool("activate_workflow", {
            "id": workflow_id,
            "active": active
        })

    async def run_workflow(self, workflow_id: str, payload: dict[str, Any] | None = None, timeout_s: int = 60) -> dict[str, Any]:
        """Execute workflow via MCP"""
        arguments = {"id": workflow_id}
        if payload:
            arguments["data"] = payload
        if timeout_s != 60:
            arguments["timeout"] = timeout_s

        return await self.execute_tool("execute_workflow", arguments)

    async def execution_status(self, execution_id: str) -> dict[str, Any]:
        """Get execution status via MCP"""
        return await self.execute_tool("get_execution", {"executionId": execution_id})

    async def list_executions(self, workflow_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        """List workflow executions via MCP"""
        arguments = {"limit": limit}
        if workflow_id:
            arguments["workflowId"] = workflow_id

        return await self.execute_tool("list_executions", arguments)

    async def get_node_types(self) -> dict[str, Any]:
        """Get available node types via MCP"""
        return await self.execute_tool("get_node_types", {})

    async def validate_workflow(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Validate workflow structure via MCP"""
        return await self.execute_tool("validate_workflow", {"workflow": workflow_data})

    async def test_workflow(self, workflow_data: dict[str, Any], test_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Test workflow execution via MCP"""
        arguments = {"workflow": workflow_data}
        if test_data:
            arguments["testData"] = test_data

        return await self.execute_tool("test_workflow", arguments)

    async def export_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Export workflow as JSON via MCP"""
        return await self.execute_tool("export_workflow", {"id": workflow_id})

    async def import_workflow(self, workflow_data: dict[str, Any], mode: str = "create") -> dict[str, Any]:
        """Import workflow JSON via MCP"""
        return await self.execute_tool("import_workflow", {
            "workflow": workflow_data,
            "mode": mode
        })

    # MCP-specific workflow operations

    async def get_workflow_schema(self) -> dict[str, Any]:
        """Get n8n workflow schema via MCP"""
        return await self.execute_tool("get_workflow_schema", {})

    async def get_credentials(self) -> dict[str, Any]:
        """Get available credentials via MCP"""
        return await self.execute_tool("list_credentials", {})

    async def create_credential(self, credential_data: dict[str, Any]) -> dict[str, Any]:
        """Create new credential via MCP"""
        return await self.execute_tool("create_credential", {"credential": credential_data})

    async def get_webhook_url(self, workflow_id: str) -> dict[str, Any]:
        """Get webhook URL for workflow via MCP"""
        return await self.execute_tool("get_webhook_url", {"workflowId": workflow_id})

    async def trigger_webhook(self, webhook_path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Trigger workflow via webhook"""
        return await self.execute_tool("trigger_webhook", {
            "path": webhook_path,
            "payload": payload
        })
