"""
Connector Manager - Connect to external data sources (Notion, Google Drive, S3, etc.)
"""

import logging
import json
import base64
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio

from ...core.config import UmbraConfig
from .errors import ContentError

logger = logging.getLogger(__name__)

@dataclass
class ConnectorConfig:
    """Configuration for external connector"""
    name: str
    type: str  # "notion", "drive", "s3", "github", "slack"
    auth_type: str  # "oauth", "api_key", "token"
    credentials: Dict[str, Any]
    enabled: bool = True
    rate_limit: Optional[int] = None

@dataclass
class Asset:
    """External asset/document"""
    id: str
    name: str
    type: str  # "document", "image", "video", "folder"
    url: Optional[str]
    content: Optional[str]
    metadata: Dict[str, Any]
    source: str  # Connector name
    last_modified: datetime

class ConnectorManager:
    """Manager for external data source connectors"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        self.connectors = {}
        self.active_connections = {}
        
        # Load available connectors
        self._load_connectors()
        
        logger.info(f"Connector manager initialized with {len(self.connectors)} connectors")
    
    def _load_connectors(self):
        """Load available connector configurations"""
        
        # Notion connector
        notion_token = self.config.get("CREATOR_NOTION_TOKEN")
        if notion_token:
            self.connectors["notion"] = ConnectorConfig(
                name="notion",
                type="notion",
                auth_type="token",
                credentials={"token": notion_token},
                enabled=True,
                rate_limit=3  # Notion API rate limit
            )
        
        # Google Drive connector
        drive_credentials = self.config.get("CREATOR_GOOGLE_DRIVE_CREDENTIALS")
        if drive_credentials:
            self.connectors["drive"] = ConnectorConfig(
                name="drive",
                type="drive",
                auth_type="oauth",
                credentials=json.loads(drive_credentials) if isinstance(drive_credentials, str) else drive_credentials,
                enabled=True,
                rate_limit=100
            )
        
        # S3/R2 connector
        s3_access_key = self.config.get("R2_ACCESS_KEY_ID")
        s3_secret_key = self.config.get("R2_SECRET_ACCESS_KEY")
        if s3_access_key and s3_secret_key:
            self.connectors["s3"] = ConnectorConfig(
                name="s3",
                type="s3",
                auth_type="api_key",
                credentials={
                    "access_key": s3_access_key,
                    "secret_key": s3_secret_key,
                    "endpoint": self.config.get("R2_ENDPOINT"),
                    "bucket": self.config.get("R2_BUCKET", "umbra")
                },
                enabled=True,
                rate_limit=1000
            )
        
        # GitHub connector
        github_token = self.config.get("CREATOR_GITHUB_TOKEN")
        if github_token:
            self.connectors["github"] = ConnectorConfig(
                name="github",
                type="github",
                auth_type="token",
                credentials={"token": github_token},
                enabled=True,
                rate_limit=5000
            )
        
        # Slack connector
        slack_token = self.config.get("CREATOR_SLACK_TOKEN")
        if slack_token:
            self.connectors["slack"] = ConnectorConfig(
                name="slack",
                type="slack",
                auth_type="token",
                credentials={"token": slack_token},
                enabled=True,
                rate_limit=20
            )
        
        # Dropbox connector
        dropbox_token = self.config.get("CREATOR_DROPBOX_TOKEN")
        if dropbox_token:
            self.connectors["dropbox"] = ConnectorConfig(
                name="dropbox",
                type="dropbox",
                auth_type="token",
                credentials={"token": dropbox_token},
                enabled=True,
                rate_limit=25
            )
    
    async def list_connectors(self) -> List[str]:
        """List available connector sources"""
        return list(self.connectors.keys())
    
    async def link_connector(self, source: str, auth: Dict[str, Any]) -> str:
        """Link to external data source"""
        try:
            if source not in self.connectors:
                raise ContentError(f"Unknown connector source: {source}", "connector")
            
            connector_config = self.connectors[source]
            
            # Test connection
            connector = await self._create_connector_instance(source, auth)
            test_result = await connector.test_connection()
            
            if not test_result["success"]:
                raise ContentError(f"Failed to connect to {source}: {test_result['error']}", "connector")
            
            # Generate connector ID
            connector_id = f"{source}_{hash(str(auth))}"
            
            # Store active connection
            self.active_connections[connector_id] = {
                "source": source,
                "connector": connector,
                "auth": auth,
                "created_at": datetime.utcnow(),
                "last_used": datetime.utcnow()
            }
            
            logger.info(f"Successfully linked connector: {source} -> {connector_id}")
            return connector_id
            
        except Exception as e:
            logger.error(f"Failed to link connector {source}: {e}")
            raise ContentError(f"Failed to link connector {source}: {e}", "connector")
    
    async def fetch_assets(self, connector_id: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch assets from connected source"""
        try:
            if connector_id not in self.active_connections:
                raise ContentError(f"Connector not found: {connector_id}", "connector")
            
            connection = self.active_connections[connector_id]
            connector = connection["connector"]
            
            # Update last used
            connection["last_used"] = datetime.utcnow()
            
            # Fetch assets
            assets = await connector.fetch_assets(query)
            
            return [self._asset_to_dict(asset) for asset in assets]
            
        except Exception as e:
            logger.error(f"Failed to fetch assets from {connector_id}: {e}")
            raise ContentError(f"Failed to fetch assets: {e}", "connector")
    
    async def get_asset_content(self, connector_id: str, asset_id: str) -> Dict[str, Any]:
        """Get full content of a specific asset"""
        try:
            if connector_id not in self.active_connections:
                raise ContentError(f"Connector not found: {connector_id}", "connector")
            
            connection = self.active_connections[connector_id]
            connector = connection["connector"]
            
            asset = await connector.get_asset_content(asset_id)
            
            return self._asset_to_dict(asset)
            
        except Exception as e:
            logger.error(f"Failed to get asset content {asset_id}: {e}")
            raise ContentError(f"Failed to get asset content: {e}", "connector")
    
    async def search_assets(self, connector_id: str, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for assets in connected source"""
        try:
            if connector_id not in self.active_connections:
                raise ContentError(f"Connector not found: {connector_id}", "connector")
            
            connection = self.active_connections[connector_id]
            connector = connection["connector"]
            
            assets = await connector.search_assets(query, filters or {})
            
            return [self._asset_to_dict(asset) for asset in assets]
            
        except Exception as e:
            logger.error(f"Failed to search assets in {connector_id}: {e}")
            raise ContentError(f"Failed to search assets: {e}", "connector")
    
    async def _create_connector_instance(self, source: str, auth: Dict[str, Any]):
        """Create connector instance"""
        if source == "notion":
            return NotionConnector(auth)
        elif source == "drive":
            return GoogleDriveConnector(auth)
        elif source == "s3":
            return S3Connector(auth)
        elif source == "github":
            return GitHubConnector(auth)
        elif source == "slack":
            return SlackConnector(auth)
        elif source == "dropbox":
            return DropboxConnector(auth)
        else:
            raise ContentError(f"Unsupported connector type: {source}", "connector")
    
    def _asset_to_dict(self, asset: Asset) -> Dict[str, Any]:
        """Convert asset to dictionary"""
        return {
            "id": asset.id,
            "name": asset.name,
            "type": asset.type,
            "url": asset.url,
            "content": asset.content,
            "metadata": asset.metadata,
            "source": asset.source,
            "last_modified": asset.last_modified.isoformat()
        }
    
    def get_connector_status(self) -> Dict[str, Any]:
        """Get status of all connectors"""
        return {
            "available_connectors": list(self.connectors.keys()),
            "active_connections": len(self.active_connections),
            "connector_details": {
                name: {
                    "type": config.type,
                    "enabled": config.enabled,
                    "auth_type": config.auth_type,
                    "has_credentials": bool(config.credentials)
                }
                for name, config in self.connectors.items()
            },
            "active_connections_details": {
                conn_id: {
                    "source": conn["source"],
                    "created_at": conn["created_at"].isoformat(),
                    "last_used": conn["last_used"].isoformat()
                }
                for conn_id, conn in self.active_connections.items()
            }
        }

# Connector Implementations

class BaseConnector:
    """Base connector interface"""
    
    def __init__(self, auth: Dict[str, Any]):
        self.auth = auth
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connector connection"""
        raise NotImplementedError
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch assets from source"""
        raise NotImplementedError
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get full content of asset"""
        raise NotImplementedError
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search for assets"""
        raise NotImplementedError

class NotionConnector(BaseConnector):
    """Notion workspace connector"""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Notion connection"""
        try:
            import httpx
            
            token = self.auth.get("token")
            if not token:
                return {"success": False, "error": "Missing Notion token"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.notion.com/v1/users/me",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Notion-Version": "2022-06-28"
                    }
                )
                
                if response.status_code == 200:
                    return {"success": True, "user": response.json()}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch Notion pages and databases"""
        try:
            import httpx
            
            token = self.auth.get("token")
            assets = []
            
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                }
                
                # Search for pages
                search_payload = {"page_size": 50}
                if query:
                    search_payload["query"] = query
                
                response = await client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json=search_payload
                )
                
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    
                    for result in results:
                        asset = Asset(
                            id=result["id"],
                            name=self._extract_notion_title(result),
                            type="document" if result["object"] == "page" else "database",
                            url=result.get("url"),
                            content=None,  # Will be fetched separately
                            metadata={
                                "notion_object": result["object"],
                                "created_time": result.get("created_time"),
                                "last_edited_time": result.get("last_edited_time"),
                                "properties": result.get("properties", {})
                            },
                            source="notion",
                            last_modified=datetime.fromisoformat(
                                result.get("last_edited_time", "").replace("Z", "+00:00")
                            ) if result.get("last_edited_time") else datetime.utcnow()
                        )
                        assets.append(asset)
                
                return assets
                
        except Exception as e:
            logger.error(f"Failed to fetch Notion assets: {e}")
            return []
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get full Notion page content"""
        try:
            import httpx
            
            token = self.auth.get("token")
            
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28"
                }
                
                # Get page info
                page_response = await client.get(
                    f"https://api.notion.com/v1/pages/{asset_id}",
                    headers=headers
                )
                
                if page_response.status_code != 200:
                    raise ContentError(f"Failed to get Notion page: {page_response.status_code}", "notion")
                
                page_data = page_response.json()
                
                # Get page content blocks
                blocks_response = await client.get(
                    f"https://api.notion.com/v1/blocks/{asset_id}/children",
                    headers=headers
                )
                
                content = ""
                if blocks_response.status_code == 200:
                    blocks = blocks_response.json().get("results", [])
                    content = self._extract_notion_content(blocks)
                
                return Asset(
                    id=asset_id,
                    name=self._extract_notion_title(page_data),
                    type="document",
                    url=page_data.get("url"),
                    content=content,
                    metadata={
                        "notion_object": "page",
                        "created_time": page_data.get("created_time"),
                        "last_edited_time": page_data.get("last_edited_time"),
                        "properties": page_data.get("properties", {})
                    },
                    source="notion",
                    last_modified=datetime.fromisoformat(
                        page_data.get("last_edited_time", "").replace("Z", "+00:00")
                    ) if page_data.get("last_edited_time") else datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to get Notion content for {asset_id}: {e}")
            raise ContentError(f"Failed to get Notion content: {e}", "notion")
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search Notion pages"""
        return await self.fetch_assets(query)
    
    def _extract_notion_title(self, page_data: Dict[str, Any]) -> str:
        """Extract title from Notion page"""
        properties = page_data.get("properties", {})
        
        # Look for title property
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0].get("text", {}).get("content", "Untitled")
        
        return f"Page {page_data.get('id', 'Unknown')[:8]}"
    
    def _extract_notion_content(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract text content from Notion blocks"""
        content_parts = []
        
        for block in blocks:
            block_type = block.get("type")
            
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                text_data = block.get(block_type, {}).get("rich_text", [])
                text = "".join([t.get("text", {}).get("content", "") for t in text_data])
                if text:
                    content_parts.append(text)
            
            elif block_type == "bulleted_list_item":
                text_data = block.get("bulleted_list_item", {}).get("rich_text", [])
                text = "".join([t.get("text", {}).get("content", "") for t in text_data])
                if text:
                    content_parts.append(f"• {text}")
            
            elif block_type == "numbered_list_item":
                text_data = block.get("numbered_list_item", {}).get("rich_text", [])
                text = "".join([t.get("text", {}).get("content", "") for t in text_data])
                if text:
                    content_parts.append(f"1. {text}")
        
        return "\n\n".join(content_parts)

class GoogleDriveConnector(BaseConnector):
    """Google Drive connector"""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Google Drive connection"""
        try:
            # Placeholder implementation
            # In real implementation, would use Google Drive API
            return {"success": True, "message": "Google Drive connector test (placeholder)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch Google Drive files"""
        # Placeholder implementation
        return []
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get Google Drive file content"""
        # Placeholder implementation
        raise ContentError("Google Drive connector not fully implemented", "drive")
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search Google Drive files"""
        return await self.fetch_assets(query)

class S3Connector(BaseConnector):
    """S3/R2 storage connector"""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test S3 connection"""
        try:
            # Use existing R2Client if available
            from ...storage.r2_client import R2Client
            
            credentials = self.auth
            r2_client = R2Client(
                account_id="",  # Not needed for basic operations
                access_key_id=credentials["access_key"],
                secret_access_key=credentials["secret_key"],
                endpoint_url=credentials.get("endpoint")
            )
            
            # Test by listing buckets or objects
            bucket = credentials.get("bucket", "umbra")
            objects = await r2_client.list_objects(bucket, max_keys=1)
            
            return {"success": True, "objects_found": len(objects)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch S3 objects"""
        try:
            from ...storage.r2_client import R2Client
            
            credentials = self.auth
            r2_client = R2Client(
                account_id="",
                access_key_id=credentials["access_key"],
                secret_access_key=credentials["secret_key"],
                endpoint_url=credentials.get("endpoint")
            )
            
            bucket = credentials.get("bucket", "umbra")
            prefix = query or ""
            
            objects = await r2_client.list_objects(bucket, prefix=prefix, max_keys=50)
            
            assets = []
            for obj in objects:
                asset = Asset(
                    id=obj["key"],
                    name=obj["key"].split("/")[-1],  # Filename
                    type=self._determine_s3_file_type(obj["key"]),
                    url=f"{credentials.get('endpoint', '')}/{bucket}/{obj['key']}",
                    content=None,
                    metadata={
                        "size": obj.get("size", 0),
                        "etag": obj.get("etag", ""),
                        "storage_class": obj.get("storage_class", "STANDARD")
                    },
                    source="s3",
                    last_modified=obj.get("last_modified", datetime.utcnow())
                )
                assets.append(asset)
            
            return assets
            
        except Exception as e:
            logger.error(f"Failed to fetch S3 assets: {e}")
            return []
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get S3 object content"""
        try:
            from ...storage.r2_client import R2Client
            
            credentials = self.auth
            r2_client = R2Client(
                account_id="",
                access_key_id=credentials["access_key"],
                secret_access_key=credentials["secret_key"],
                endpoint_url=credentials.get("endpoint")
            )
            
            bucket = credentials.get("bucket", "umbra")
            
            # Get object content
            content_data = await r2_client.get_object(bucket, asset_id)
            
            # Try to decode as text if possible
            content = None
            if content_data:
                try:
                    content = content_data.decode('utf-8')
                except UnicodeDecodeError:
                    # Binary file - encode as base64
                    content = base64.b64encode(content_data).decode('ascii')
            
            return Asset(
                id=asset_id,
                name=asset_id.split("/")[-1],
                type=self._determine_s3_file_type(asset_id),
                url=f"{credentials.get('endpoint', '')}/{bucket}/{asset_id}",
                content=content,
                metadata={"bucket": bucket},
                source="s3",
                last_modified=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get S3 content for {asset_id}: {e}")
            raise ContentError(f"Failed to get S3 content: {e}", "s3")
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search S3 objects"""
        return await self.fetch_assets(query)
    
    def _determine_s3_file_type(self, key: str) -> str:
        """Determine file type from S3 key"""
        extension = key.split(".")[-1].lower() if "." in key else ""
        
        if extension in ["jpg", "jpeg", "png", "gif", "webp"]:
            return "image"
        elif extension in ["mp4", "mov", "avi", "webm"]:
            return "video"
        elif extension in ["mp3", "wav", "m4a", "ogg"]:
            return "audio"
        elif extension in ["txt", "md", "json", "csv"]:
            return "document"
        else:
            return "file"

class GitHubConnector(BaseConnector):
    """GitHub repository connector"""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test GitHub connection"""
        try:
            import httpx
            
            token = self.auth.get("token")
            if not token:
                return {"success": False, "error": "Missing GitHub token"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {"success": True, "user": user_data.get("login")}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch GitHub repositories and files"""
        # Placeholder implementation
        return []
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get GitHub file content"""
        # Placeholder implementation
        raise ContentError("GitHub connector not fully implemented", "github")
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search GitHub repositories"""
        return await self.fetch_assets(query)

class SlackConnector(BaseConnector):
    """Slack workspace connector"""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Slack connection"""
        try:
            import httpx
            
            token = self.auth.get("token")
            if not token:
                return {"success": False, "error": "Missing Slack token"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return {"success": True, "team": data.get("team")}
                    else:
                        return {"success": False, "error": data.get("error")}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch Slack messages and files"""
        # Placeholder implementation
        return []
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get Slack message/file content"""
        # Placeholder implementation
        raise ContentError("Slack connector not fully implemented", "slack")
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search Slack messages"""
        return await self.fetch_assets(query)

class DropboxConnector(BaseConnector):
    """Dropbox connector"""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Dropbox connection"""
        try:
            import httpx
            
            token = self.auth.get("token")
            if not token:
                return {"success": False, "error": "Missing Dropbox token"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    "https://api.dropboxapi.com/2/users/get_current_account",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {"success": True, "user": user_data.get("name", {}).get("display_name")}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_assets(self, query: Optional[str] = None) -> List[Asset]:
        """Fetch Dropbox files"""
        # Placeholder implementation
        return []
    
    async def get_asset_content(self, asset_id: str) -> Asset:
        """Get Dropbox file content"""
        # Placeholder implementation
        raise ContentError("Dropbox connector not fully implemented", "dropbox")
    
    async def search_assets(self, query: str, filters: Dict[str, Any]) -> List[Asset]:
        """Search Dropbox files"""
        return await self.fetch_assets(query)
