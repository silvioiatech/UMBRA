"""
Export Manager - Bundle and export content with R2 storage integration
Saves outputs to R2 and returns presigned URLs for Telegram delivery
"""

import asyncio
import json
import logging
import zipfile
import tempfile
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from ...core.config import UmbraConfig
from ...storage.r2_client import R2Client
from .errors import ExportError

logger = logging.getLogger(__name__)

@dataclass
class ExportAsset:
    """Asset for export bundle"""
    type: str  # 'text', 'image', 'video', 'audio', 'code'
    url: str
    meta: Dict[str, Any]
    filename: Optional[str] = None
    content: Optional[str] = None  # For text assets

@dataclass
class ExportBundle:
    """Complete export bundle"""
    assets: List[ExportAsset]
    format_type: str  # 'zip', 'json', 'md'
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: datetime

class ExportManager:
    """Handles content bundling and export to R2 storage"""
    
    def __init__(self, config: UmbraConfig, r2_client: Optional[R2Client] = None):
        self.config = config
        self.r2_client = r2_client
        
        # Export settings
        self.bucket_name = config.get("R2_BUCKET", "umbra")
        self.export_prefix = "creator/exports"
        self.default_expiry_hours = config.get("CREATOR_EXPORT_EXPIRY_HOURS", 24)
        self.max_bundle_size = config.get("CREATOR_MAX_BUNDLE_SIZE_MB", 100) * 1024 * 1024
        
        # File size limits
        self.max_file_sizes = {
            "image": 10 * 1024 * 1024,  # 10MB
            "video": 100 * 1024 * 1024,  # 100MB
            "audio": 50 * 1024 * 1024,   # 50MB
            "text": 1 * 1024 * 1024,     # 1MB
            "code": 5 * 1024 * 1024      # 5MB
        }
        
        logger.info("Export manager initialized")
    
    async def create_bundle(self, assets: List[Dict[str, Any]], 
                          format_type: str = "zip", 
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create and upload export bundle to R2"""
        try:
            if not self.r2_client:
                raise ExportError("R2 client not configured", format_type)
            
            if not assets:
                raise ExportError("No assets provided for export", format_type)
            
            # Validate format type
            if format_type not in ["zip", "json", "md"]:
                raise ExportError(f"Unsupported format type: {format_type}", format_type)
            
            # Parse and validate assets
            export_assets = await self._parse_assets(assets)
            
            # Check total bundle size
            total_size = await self._calculate_bundle_size(export_assets)
            if total_size > self.max_bundle_size:
                raise ExportError(f"Bundle size ({total_size} bytes) exceeds limit ({self.max_bundle_size} bytes)", format_type)
            
            # Create bundle
            bundle_data = await self._create_bundle_data(export_assets, format_type, metadata or {})
            
            # Generate unique filename
            bundle_filename = self._generate_bundle_filename(format_type)
            bundle_key = f"{self.export_prefix}/{bundle_filename}"
            
            # Upload to R2
            await self.r2_client.put_object(
                bucket=self.bucket_name,
                key=bundle_key,
                data=bundle_data,
                content_type=self._get_content_type(format_type),
                metadata={
                    "creator": "umbra-creator",
                    "format": format_type,
                    "asset_count": str(len(export_assets)),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Generate presigned URL
            presigned_url = await self.r2_client.generate_presigned_url(
                bucket=self.bucket_name,
                key=bundle_key,
                expires_in=self.default_expiry_hours * 3600,
                method="GET"
            )
            
            logger.info(f"Export bundle created: {bundle_filename}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"Bundle creation failed: {e}")
            raise ExportError(f"Bundle creation failed: {e}", format_type)
    
    async def _parse_assets(self, assets: List[Dict[str, Any]]) -> List[ExportAsset]:
        """Parse and validate asset list"""
        parsed_assets = []
        
        for i, asset in enumerate(assets):
            try:
                asset_type = asset.get("type")
                if not asset_type:
                    raise ExportError(f"Asset {i}: type is required")
                
                url = asset.get("url")
                content = asset.get("content")
                
                if not url and not content:
                    raise ExportError(f"Asset {i}: url or content is required")
                
                meta = asset.get("meta", {})
                filename = asset.get("filename") or self._generate_asset_filename(asset_type, meta)
                
                export_asset = ExportAsset(
                    type=asset_type,
                    url=url or "",
                    meta=meta,
                    filename=filename,
                    content=content
                )
                
                parsed_assets.append(export_asset)
                
            except Exception as e:
                raise ExportError(f"Asset {i} parsing failed: {e}")
        
        return parsed_assets
    
    async def _calculate_bundle_size(self, assets: List[ExportAsset]) -> int:
        """Calculate total bundle size"""
        total_size = 0
        
        for asset in assets:
            if asset.content:
                # Text content size
                total_size += len(asset.content.encode('utf-8'))
            elif asset.url:
                # Estimate from metadata or use default
                file_size = asset.meta.get("size", 0)
                if not file_size:
                    # Default estimates by type
                    default_sizes = {
                        "image": 500_000,    # 500KB
                        "video": 10_000_000, # 10MB
                        "audio": 5_000_000,  # 5MB
                        "text": 10_000,      # 10KB
                        "code": 50_000       # 50KB
                    }
                    file_size = default_sizes.get(asset.type, 100_000)
                
                total_size += file_size
        
        return total_size
    
    async def _create_bundle_data(self, assets: List[ExportAsset], 
                                format_type: str, metadata: Dict[str, Any]) -> bytes:
        """Create bundle data in specified format"""
        if format_type == "zip":
            return await self._create_zip_bundle(assets, metadata)
        elif format_type == "json":
            return await self._create_json_bundle(assets, metadata)
        elif format_type == "md":
            return await self._create_markdown_bundle(assets, metadata)
        else:
            raise ExportError(f"Unsupported format: {format_type}", format_type)
    
    async def _create_zip_bundle(self, assets: List[ExportAsset], metadata: Dict[str, Any]) -> bytes:
        """Create ZIP bundle"""
        with tempfile.NamedTemporaryFile() as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add metadata file
                metadata_content = {
                    "bundle_info": {
                        "created_at": datetime.utcnow().isoformat(),
                        "format": "zip",
                        "asset_count": len(assets),
                        "creator": "umbra-creator"
                    },
                    "user_metadata": metadata,
                    "assets": []
                }
                
                # Process each asset
                for i, asset in enumerate(assets):
                    try:
                        if asset.content:
                            # Add text content directly
                            zip_file.writestr(asset.filename, asset.content.encode('utf-8'))
                        elif asset.url:
                            # Download and add file
                            file_data = await self._download_asset(asset.url)
                            if file_data:
                                zip_file.writestr(asset.filename, file_data)
                        
                        # Add to metadata
                        metadata_content["assets"].append({
                            "filename": asset.filename,
                            "type": asset.type,
                            "meta": asset.meta
                        })
                        
                    except Exception as e:
                        logger.warning(f"Failed to add asset {i} to ZIP: {e}")
                        # Continue with other assets
                
                # Add metadata file
                zip_file.writestr("bundle_metadata.json", 
                                json.dumps(metadata_content, indent=2).encode('utf-8'))
            
            temp_file.seek(0)
            return temp_file.read()
    
    async def _create_json_bundle(self, assets: List[ExportAsset], metadata: Dict[str, Any]) -> bytes:
        """Create JSON bundle"""
        bundle_data = {
            "bundle_info": {
                "created_at": datetime.utcnow().isoformat(),
                "format": "json",
                "asset_count": len(assets),
                "creator": "umbra-creator"
            },
            "metadata": metadata,
            "assets": []
        }
        
        for asset in assets:
            asset_data = {
                "type": asset.type,
                "filename": asset.filename,
                "meta": asset.meta
            }
            
            if asset.content:
                asset_data["content"] = asset.content
            elif asset.url:
                asset_data["url"] = asset.url
            
            bundle_data["assets"].append(asset_data)
        
        return json.dumps(bundle_data, indent=2).encode('utf-8')
    
    async def _create_markdown_bundle(self, assets: List[ExportAsset], metadata: Dict[str, Any]) -> bytes:
        """Create Markdown bundle"""
        md_content = []
        
        # Header with metadata
        md_content.append("# Content Bundle")
        md_content.append("")
        md_content.append("## Bundle Information")
        md_content.append(f"- Created: {datetime.utcnow().isoformat()}")
        md_content.append(f"- Format: Markdown")
        md_content.append(f"- Assets: {len(assets)}")
        md_content.append(f"- Creator: Umbra Creator")
        md_content.append("")
        
        # User metadata
        if metadata:
            md_content.append("## Metadata")
            for key, value in metadata.items():
                md_content.append(f"- **{key}**: {value}")
            md_content.append("")
        
        # Assets
        md_content.append("## Assets")
        md_content.append("")
        
        for i, asset in enumerate(assets, 1):
            md_content.append(f"### {i}. {asset.filename}")
            md_content.append(f"**Type**: {asset.type}")
            
            if asset.meta:
                md_content.append("**Metadata**:")
                for key, value in asset.meta.items():
                    md_content.append(f"- {key}: {value}")
            
            if asset.content:
                md_content.append("**Content**:")
                md_content.append("```")
                md_content.append(asset.content)
                md_content.append("```")
            elif asset.url:
                md_content.append(f"**URL**: {asset.url}")
            
            md_content.append("")
        
        return "\n".join(md_content).encode('utf-8')
    
    async def _download_asset(self, url: str) -> Optional[bytes]:
        """Download asset from URL"""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"Failed to download asset: {url} (status: {response.status_code})")
                    return None
                    
        except Exception as e:
            logger.warning(f"Failed to download asset: {url} ({e})")
            return None
    
    def _generate_bundle_filename(self, format_type: str) -> str:
        """Generate unique bundle filename"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.md5(f"{timestamp}_{format_type}".encode()).hexdigest()[:8]
        return f"bundle_{timestamp}_{hash_part}.{format_type}"
    
    def _generate_asset_filename(self, asset_type: str, meta: Dict[str, Any]) -> str:
        """Generate filename for asset"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Try to get original filename from meta
        original_name = meta.get("filename") or meta.get("name")
        if original_name:
            name_part = Path(original_name).stem
            extension = Path(original_name).suffix
        else:
            name_part = f"{asset_type}_{timestamp}"
            extension = self._get_default_extension(asset_type)
        
        return f"{name_part}_{timestamp}{extension}"
    
    def _get_default_extension(self, asset_type: str) -> str:
        """Get default file extension for asset type"""
        extensions = {
            "image": ".png",
            "video": ".mp4",
            "audio": ".mp3",
            "text": ".txt",
            "code": ".py",
            "json": ".json",
            "markdown": ".md"
        }
        return extensions.get(asset_type, ".bin")
    
    def _get_content_type(self, format_type: str) -> str:
        """Get MIME content type for format"""
        content_types = {
            "zip": "application/zip",
            "json": "application/json",
            "md": "text/markdown"
        }
        return content_types.get(format_type, "application/octet-stream")
    
    async def save_single_asset(self, asset_data: bytes, asset_type: str, 
                              filename: Optional[str] = None, 
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save single asset to R2 and return presigned URL"""
        try:
            if not self.r2_client:
                raise ExportError("R2 client not configured", asset_type)
            
            # Validate file size
            max_size = self.max_file_sizes.get(asset_type, 10 * 1024 * 1024)
            if len(asset_data) > max_size:
                raise ExportError(f"Asset size ({len(asset_data)} bytes) exceeds limit ({max_size} bytes)", asset_type)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                extension = self._get_default_extension(asset_type)
                filename = f"{asset_type}_{timestamp}{extension}"
            
            # Upload to R2
            asset_key = f"{self.export_prefix}/assets/{filename}"
            
            await self.r2_client.put_object(
                bucket=self.bucket_name,
                key=asset_key,
                data=asset_data,
                content_type=self._get_asset_content_type(asset_type),
                metadata={
                    "creator": "umbra-creator",
                    "asset_type": asset_type,
                    "created_at": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )
            
            # Generate presigned URL
            presigned_url = await self.r2_client.generate_presigned_url(
                bucket=self.bucket_name,
                key=asset_key,
                expires_in=self.default_expiry_hours * 3600,
                method="GET"
            )
            
            logger.info(f"Asset saved: {filename}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"Asset save failed: {e}")
            raise ExportError(f"Asset save failed: {e}", asset_type)
    
    def _get_asset_content_type(self, asset_type: str) -> str:
        """Get MIME content type for asset type"""
        content_types = {
            "image": "image/png",
            "video": "video/mp4",
            "audio": "audio/mpeg",
            "text": "text/plain",
            "code": "text/plain",
            "json": "application/json",
            "markdown": "text/markdown"
        }
        return content_types.get(asset_type, "application/octet-stream")
    
    async def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics"""
        try:
            if not self.r2_client:
                return {"error": "R2 client not configured"}
            
            # List exports (limited to recent ones)
            objects = await self.r2_client.list_objects(
                bucket=self.bucket_name,
                prefix=self.export_prefix,
                max_keys=100
            )
            
            total_exports = len(objects)
            total_size = sum(obj.get('size', 0) for obj in objects)
            
            # Group by date
            exports_by_date = {}
            for obj in objects:
                date_str = obj.get('last_modified', '')[:10]  # YYYY-MM-DD
                if date_str not in exports_by_date:
                    exports_by_date[date_str] = 0
                exports_by_date[date_str] += 1
            
            return {
                "total_exports": total_exports,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "exports_by_date": exports_by_date,
                "bucket": self.bucket_name,
                "prefix": self.export_prefix
            }
            
        except Exception as e:
            logger.error(f"Failed to get export stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired_exports(self) -> Dict[str, Any]:
        """Clean up expired exports"""
        try:
            if not self.r2_client:
                return {"error": "R2 client not configured"}
            
            cutoff_date = datetime.utcnow() - timedelta(days=7)  # Keep for 7 days
            
            objects = await self.r2_client.list_objects(
                bucket=self.bucket_name,
                prefix=self.export_prefix
            )
            
            deleted_count = 0
            deleted_size = 0
            
            for obj in objects:
                obj_date = datetime.fromisoformat(obj.get('last_modified', '').replace('Z', '+00:00'))
                if obj_date < cutoff_date:
                    await self.r2_client.delete_object(
                        bucket=self.bucket_name,
                        key=obj['key']
                    )
                    deleted_count += 1
                    deleted_size += obj.get('size', 0)
            
            return {
                "deleted_exports": deleted_count,
                "freed_space_mb": round(deleted_size / (1024 * 1024), 2),
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"error": str(e)}
