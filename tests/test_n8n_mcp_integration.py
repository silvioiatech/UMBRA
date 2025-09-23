"""
Test N8n MCP Client Integration

Tests the new MCP client for n8n integration with the Railway-hosted MCP server.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch

from umbra.core.config import UmbraConfig
from umbra.modules.production.n8n_mcp_client import N8nMCPClient, N8nMCPCredentials


class TestN8nMCPClient:
    """Test N8n MCP Client functionality"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        config = Mock(spec=UmbraConfig)
        config.get.side_effect = lambda key, default=None: {
            'N8N_MCP_SERVER_URL': 'https://test-n8n-mcp.railway.app',
            'N8N_MCP_API_KEY': 'test-mcp-key',
            'N8N_MCP_AUTH_TOKEN': None,
            'MAIN_N8N_URL': None,
            'N8N_API_KEY': None
        }.get(key, default)
        return config

    @pytest.fixture
    def mcp_client(self, mock_config):
        """Create MCP client for testing"""
        return N8nMCPClient(mock_config)

    def test_credentials_loading_api_key(self, mock_config):
        """Test loading credentials with API key"""
        client = N8nMCPClient(mock_config)
        assert client.credentials.api_key == 'test-mcp-key'
        assert client.credentials.auth_type == 'api_key'

    def test_credentials_loading_fallback(self):
        """Test credentials fallback to n8n API key"""
        config = Mock(spec=UmbraConfig)
        config.get.side_effect = lambda key, default=None: {
            'N8N_MCP_SERVER_URL': 'https://test.railway.app',
            'N8N_MCP_API_KEY': None,
            'N8N_MCP_AUTH_TOKEN': None,
            'N8N_API_KEY': 'fallback-key'
        }.get(key, default)
        
        client = N8nMCPClient(config)
        assert client.credentials.api_key == 'fallback-key'
        assert client.credentials.auth_type == 'api_key'

    def test_server_url_resolution(self, mock_config):
        """Test server URL resolution"""
        client = N8nMCPClient(mock_config)
        assert client.server_url == 'https://test-n8n-mcp.railway.app'

    @pytest.mark.asyncio
    async def test_health_check_success(self, mcp_client):
        """Test successful health check"""
        mock_response = {'status': 'ok', 'version': '1.0.0'}
        
        with patch.object(mcp_client, '_request', return_value=mock_response) as mock_request:
            result = await mcp_client.health_check()
            
            assert result['status'] == 'healthy'
            assert result['data'] == mock_response
            mock_request.assert_called_once_with('GET', '/health')

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mcp_client):
        """Test health check failure handling"""
        with patch.object(mcp_client, '_request', side_effect=Exception('Connection failed')):
            result = await mcp_client.health_check()
            
            assert result['status'] == 'unhealthy'
            assert 'Connection failed' in result['error']

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """Test listing available MCP tools"""
        mock_tools = [
            {'name': 'list_workflows', 'description': 'List n8n workflows'},
            {'name': 'create_workflow', 'description': 'Create new workflow'}
        ]
        mock_response = {'tools': mock_tools}
        
        with patch.object(mcp_client, '_request', return_value=mock_response):
            tools = await mcp_client.list_tools()
            
            assert len(tools) == 2
            assert tools[0]['name'] == 'list_workflows'

    @pytest.mark.asyncio
    async def test_execute_tool(self, mcp_client):
        """Test tool execution via MCP"""
        mock_result = {'success': True, 'data': {'workflow_id': '123'}}
        
        with patch.object(mcp_client, '_request', return_value=mock_result) as mock_request:
            result = await mcp_client.execute_tool('create_workflow', {'name': 'Test Workflow'})
            
            assert result == mock_result
            mock_request.assert_called_once_with('POST', '/mcp/execute', json={
                'name': 'create_workflow',
                'arguments': {'name': 'Test Workflow'}
            })

    @pytest.mark.asyncio
    async def test_list_workflows(self, mcp_client):
        """Test listing workflows via MCP"""
        mock_result = {'workflows': [{'id': '1', 'name': 'Test Workflow'}]}
        
        with patch.object(mcp_client, 'execute_tool', return_value=mock_result):
            result = await mcp_client.list_workflows(query='test', limit=10)
            
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_get_workflow(self, mcp_client):
        """Test getting specific workflow via MCP"""
        mock_result = {'workflow': {'id': '123', 'name': 'Test Workflow'}}
        
        with patch.object(mcp_client, 'execute_tool', return_value=mock_result) as mock_execute:
            result = await mcp_client.get_workflow(workflow_id='123')
            
            mock_execute.assert_called_once_with('get_workflow', {'id': '123'})
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_create_workflow(self, mcp_client):
        """Test creating workflow via MCP"""
        workflow_data = {'name': 'New Workflow', 'nodes': []}
        mock_result = {'success': True, 'workflow_id': '456'}
        
        with patch.object(mcp_client, 'execute_tool', return_value=mock_result) as mock_execute:
            result = await mcp_client.create_workflow(workflow_data)
            
            mock_execute.assert_called_once_with('create_workflow', {'workflow': workflow_data})
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_run_workflow(self, mcp_client):
        """Test running workflow via MCP"""
        payload = {'input': 'test data'}
        mock_result = {'execution_id': '789', 'status': 'running'}
        
        with patch.object(mcp_client, 'execute_tool', return_value=mock_result) as mock_execute:
            result = await mcp_client.run_workflow('123', payload, timeout_s=30)
            
            expected_args = {'id': '123', 'data': payload, 'timeout': 30}
            mock_execute.assert_called_once_with('execute_workflow', expected_args)
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_session_management(self, mcp_client):
        """Test HTTP session creation and management"""
        session = await mcp_client._get_session()
        
        assert session is not None
        assert 'Authorization' in session._default_headers
        assert session._default_headers['Authorization'] == 'Bearer test-mcp-key'
        
        # Test session reuse
        session2 = await mcp_client._get_session()
        assert session is session2
        
        # Test session cleanup
        await mcp_client.close()
        assert mcp_client.session is None

    @pytest.mark.asyncio
    async def test_error_handling(self, mcp_client):
        """Test error handling in tool execution"""
        with patch.object(mcp_client, '_request', side_effect=Exception('MCP server error')):
            result = await mcp_client.execute_tool('failing_tool', {})
            
            assert result['error'] == 'MCP server error'
            assert result['success'] is False


class TestN8nMCPIntegration:
    """Integration tests for N8n MCP functionality"""

    @pytest.mark.asyncio
    async def test_production_module_integration(self):
        """Test integration with production module"""
        # This would be an integration test that verifies the production module
        # can successfully use the MCP client instead of direct n8n client
        
        # Mock config with MCP settings
        config = Mock(spec=UmbraConfig)
        config.get.side_effect = lambda key, default=None: {
            'N8N_MCP_SERVER_URL': 'https://test-mcp.railway.app',
            'N8N_MCP_API_KEY': 'test-key'
        }.get(key, default)
        
        # Create MCP client
        mcp_client = N8nMCPClient(config)
        
        # Verify client is properly configured
        assert mcp_client.server_url == 'https://test-mcp.railway.app'
        assert mcp_client.credentials.api_key == 'test-key'
        
        await mcp_client.close()


if __name__ == '__main__':
    # Run basic tests
    print("🧪 Testing N8n MCP Client Integration")
    
    # Test credentials creation
    creds = N8nMCPCredentials(api_key='test-key', auth_type='api_key')
    assert creds.api_key == 'test-key'
    print("✅ Credentials test passed")
    
    # Test config mock
    config = Mock()
    config.get.return_value = 'https://test.railway.app'
    client = N8nMCPClient(config)
    assert client.server_url == 'https://test.railway.app'
    print("✅ Client initialization test passed")
    
    print("🎉 All basic tests passed! Run with pytest for full test suite.")