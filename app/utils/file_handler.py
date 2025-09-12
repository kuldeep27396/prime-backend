"""
File handling utilities for video uploads and storage
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

try:
    import aiofiles
    import aiohttp
    ASYNC_DEPS_AVAILABLE = True
except ImportError:
    ASYNC_DEPS_AVAILABLE = False

from fastapi import HTTPException, status

try:
    from app.core.config import settings
except ImportError:
    # For testing without full app context
    class MockSettings:
        BLOB_READ_WRITE_TOKEN = None
        API_BASE_URL = "http://localhost:8000"
    settings = MockSettings()


class FileHandler:
    """Handle file uploads and storage operations"""

    def __init__(self):
        self.vercel_blob_token = settings.BLOB_READ_WRITE_TOKEN
        self.vercel_blob_url = "https://blob.vercel-storage.com"

    async def generate_upload_url(
        self,
        filename: str,
        content_type: str = "video/webm",
        expires_in_hours: int = 1
    ) -> Dict[str, str]:
        """Generate a pre-signed URL for file upload to Vercel Blob"""
        
        if not self.vercel_blob_token or not ASYNC_DEPS_AVAILABLE:
            # Fallback to local storage for development
            return await self._generate_local_upload_url(filename)

        try:
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Create upload URL request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.vercel_blob_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "pathname": unique_filename,
                    "access": "public",
                    "addRandomSuffix": False
                }
                
                async with session.post(
                    f"{self.vercel_blob_url}/upload",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to generate upload URL"
                        )
                    
                    data = await response.json()
                    
                    return {
                        "upload_url": data.get("url"),
                        "media_url": data.get("downloadUrl"),
                        "filename": unique_filename,
                        "expires_at": (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat()
                    }
                    
        except Exception as e:
            print(f"Error generating upload URL: {e}")
            # Fallback to local storage
            return await self._generate_local_upload_url(filename)

    async def _generate_local_upload_url(self, filename: str) -> Dict[str, str]:
        """Generate local upload URL for development"""
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # For local development, we'll use the same URL for upload and access
        base_url = settings.API_BASE_URL or "http://localhost:8000"
        media_url = f"{base_url}/uploads/videos/{unique_filename}"
        
        return {
            "upload_url": media_url,  # In real implementation, this would be different
            "media_url": media_url,
            "filename": unique_filename,
            "local_path": file_path,
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

    async def save_local_file(self, file_path: str, content: bytes) -> bool:
        """Save file locally for development"""
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file
            if ASYNC_DEPS_AVAILABLE:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
            else:
                with open(file_path, 'wb') as f:
                    f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error saving local file: {e}")
            return False

    async def delete_file(self, media_url: str) -> bool:
        """Delete file from storage"""
        
        if not self.vercel_blob_token or not ASYNC_DEPS_AVAILABLE:
            # Delete local file
            return await self._delete_local_file(media_url)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.vercel_blob_token}"
                }
                
                async with session.delete(
                    media_url,
                    headers=headers
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    async def _delete_local_file(self, media_url: str) -> bool:
        """Delete local file"""
        
        try:
            # Extract filename from URL
            filename = media_url.split('/')[-1]
            file_path = os.path.join("uploads/videos", filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting local file: {e}")
            return False

    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get file information"""
        
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                return {
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime),
                    "exists": True
                }
            else:
                return {"exists": False}
                
        except Exception as e:
            print(f"Error getting file info: {e}")
            return {"exists": False, "error": str(e)}

    async def validate_video_file(self, content: bytes, max_size_mb: int = 100) -> Dict[str, any]:
        """Validate video file content"""
        
        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > max_size_mb:
            return {
                "valid": False,
                "error": f"File size ({size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            }
        
        # Check file signature (basic validation)
        video_signatures = [
            b'\x1a\x45\xdf\xa3',  # WebM
            b'\x00\x00\x00\x18ftypmp4',  # MP4
            b'\x00\x00\x00\x20ftypmp4',  # MP4
            b'RIFF',  # AVI (starts with RIFF)
        ]
        
        is_video = any(content.startswith(sig) for sig in video_signatures)
        
        if not is_video:
            return {
                "valid": False,
                "error": "File does not appear to be a valid video format"
            }
        
        return {
            "valid": True,
            "size_mb": size_mb,
            "estimated_duration": None  # Could be implemented with ffprobe
        }


# Global file handler instance
file_handler = FileHandler()