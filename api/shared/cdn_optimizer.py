"""
CDN Integration and Static Asset Optimization - Task 3.2 Performance Optimization
Implements CDN configuration, asset optimization, and caching strategies
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

class CDNOptimizer:
    """
    CDN integration and static asset optimization service
    """
    
    def __init__(self):
        self.cdn_config = self._load_cdn_config()
        self.asset_cache = {}
        self.compression_enabled = True
        self.cache_busting_enabled = True
        
    def _load_cdn_config(self) -> Dict[str, Any]:
        """Load CDN configuration from environment or config file"""
        return {
            "enabled": os.getenv("CDN_ENABLED", "false").lower() == "true",
            "base_url": os.getenv("CDN_BASE_URL", "https://cdn.sutra.vedprakash.net"),
            "api_key": os.getenv("CDN_API_KEY", ""),
            "zones": {
                "static": os.getenv("CDN_STATIC_ZONE", "static"),
                "images": os.getenv("CDN_IMAGES_ZONE", "images"),
                "scripts": os.getenv("CDN_SCRIPTS_ZONE", "js"),
                "styles": os.getenv("CDN_STYLES_ZONE", "css")
            },
            "cache_control": {
                "static": "max-age=31536000, immutable",  # 1 year for static assets
                "images": "max-age=2592000",  # 30 days for images
                "scripts": "max-age=31536000, immutable",  # 1 year for JS
                "styles": "max-age=31536000, immutable"  # 1 year for CSS
            }
        }
    
    def get_asset_url(self, asset_path: str, asset_type: str = "static") -> str:
        """Get CDN URL for an asset with cache busting if enabled"""
        
        if not self.cdn_config["enabled"]:
            # Return local asset path if CDN is disabled
            return f"/assets/{asset_path}"
        
        # Generate cache-busting hash if enabled
        cache_bust = ""
        if self.cache_busting_enabled:
            cache_bust = self._generate_cache_bust(asset_path)
        
        # Build CDN URL
        zone = self.cdn_config["zones"].get(asset_type, "static")
        base_url = self.cdn_config["base_url"].rstrip("/")
        
        if cache_bust:
            asset_path_with_hash = f"{asset_path}?v={cache_bust}"
        else:
            asset_path_with_hash = asset_path
        
        cdn_url = f"{base_url}/{zone}/{asset_path_with_hash}"
        
        logging.debug(f"Generated CDN URL: {cdn_url}")
        return cdn_url
    
    def _generate_cache_bust(self, asset_path: str) -> str:
        """Generate cache-busting hash for an asset"""
        
        # Try to get file modification time for cache busting
        local_path = Path(f"./public/{asset_path}")
        
        if local_path.exists():
            # Use file modification time + size for hash
            stat = local_path.stat()
            hash_input = f"{asset_path}:{stat.st_mtime}:{stat.st_size}"
        else:
            # Fallback to asset path + current deployment
            deployment_id = os.getenv("DEPLOYMENT_ID", "dev")
            hash_input = f"{asset_path}:{deployment_id}"
        
        # Generate short hash
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """Get optimization configuration for build tools"""
        
        config = {
            "compression": {
                "enabled": self.compression_enabled,
                "gzip": True,
                "brotli": True,
                "threshold": 1024  # Compress files > 1KB
            },
            "minification": {
                "javascript": True,
                "css": True,
                "html": True
            },
            "image_optimization": {
                "enabled": True,
                "formats": ["webp", "avif"],
                "quality": 85,
                "progressive_jpeg": True
            },
            "preloading": {
                "critical_resources": [
                    "/css/main.css",
                    "/js/app.js",
                    "/fonts/inter-var.woff2"
                ],
                "prefetch_on_hover": True
            },
            "caching": {
                "service_worker": True,
                "cache_strategy": "cache_first",
                "runtime_caching": [
                    {
                        "pattern": "^https://api\\.",
                        "strategy": "network_first",
                        "cache_name": "api-cache"
                    },
                    {
                        "pattern": "\\.(png|jpg|jpeg|svg|gif)$",
                        "strategy": "cache_first",
                        "cache_name": "images-cache"
                    }
                ]
            }
        }
        
        return config
    
    def generate_asset_manifest(self, build_dir: str = "./dist") -> Dict[str, str]:
        """Generate asset manifest for cache busting"""
        
        manifest = {}
        build_path = Path(build_dir)
        
        if not build_path.exists():
            logging.warning(f"Build directory {build_dir} not found")
            return manifest
        
        # Find all static assets
        asset_patterns = ["**/*.js", "**/*.css", "**/*.png", "**/*.jpg", "**/*.svg", "**/*.woff2"]
        
        for pattern in asset_patterns:
            for asset_file in build_path.glob(pattern):
                # Get relative path from build dir
                relative_path = asset_file.relative_to(build_path)
                
                # Generate hash for the file
                file_hash = self._hash_file(asset_file)
                
                # Store original -> hashed mapping
                manifest[str(relative_path)] = f"{relative_path.stem}.{file_hash[:8]}{relative_path.suffix}"
        
        # Save manifest file
        manifest_path = build_path / "asset-manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logging.info(f"Generated asset manifest with {len(manifest)} entries")
        return manifest
    
    def _hash_file(self, file_path: Path) -> str:
        """Generate hash for file contents"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def get_performance_headers(self, asset_type: str) -> Dict[str, str]:
        """Get performance-optimized headers for asset types"""
        
        base_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        # Add cache control based on asset type
        cache_control = self.cdn_config["cache_control"].get(asset_type, "max-age=3600")
        base_headers["Cache-Control"] = cache_control
        
        # Add compression headers
        if self.compression_enabled:
            base_headers["Vary"] = "Accept-Encoding"
        
        # Asset-specific headers
        if asset_type == "scripts":
            base_headers["X-JavaScript-Enabled"] = "true"
        elif asset_type == "styles":
            base_headers["X-CSS-Optimized"] = "true"
        elif asset_type == "images":
            base_headers["Accept"] = "image/webp,image/avif,image/*,*/*;q=0.8"
        
        return base_headers
    
    def get_preload_links(self, critical_resources: Optional[List[str]] = None) -> List[str]:
        """Generate preload link headers for critical resources"""
        
        if not critical_resources:
            critical_resources = self.get_optimization_config()["preloading"]["critical_resources"]
        
        preload_links = []
        
        for resource in critical_resources:
            # Determine resource type
            if resource.endswith('.css'):
                resource_type = 'style'
                as_type = 'style'
            elif resource.endswith('.js'):
                resource_type = 'script'
                as_type = 'script'
            elif resource.endswith(('.woff', '.woff2')):
                resource_type = 'font'
                as_type = 'font'
            elif resource.endswith(('.png', '.jpg', '.webp')):
                resource_type = 'image'
                as_type = 'image'
            else:
                continue
            
            # Get CDN URL
            cdn_url = self.get_asset_url(resource.lstrip('/'), resource_type)
            
            # Build preload link
            preload_link = f'<{cdn_url}>; rel=preload; as={as_type}'
            
            if as_type == 'font':
                preload_link += '; crossorigin'
            
            preload_links.append(preload_link)
        
        return preload_links
    
    def get_cdn_stats(self) -> Dict[str, Any]:
        """Get CDN performance statistics"""
        
        return {
            "enabled": self.cdn_config["enabled"],
            "base_url": self.cdn_config["base_url"],
            "zones_configured": len(self.cdn_config["zones"]),
            "cache_busting": self.cache_busting_enabled,
            "compression": self.compression_enabled,
            "cache_controls": self.cdn_config["cache_control"],
            "optimization_features": {
                "gzip_compression": True,
                "brotli_compression": True,
                "image_optimization": True,
                "minification": True,
                "preloading": True,
                "service_worker_caching": True
            }
        }

# Global CDN optimizer instance
_cdn_optimizer = None

def get_cdn_optimizer() -> CDNOptimizer:
    """Get singleton CDN optimizer"""
    global _cdn_optimizer
    if _cdn_optimizer is None:
        _cdn_optimizer = CDNOptimizer()
    return _cdn_optimizer

def optimize_static_assets():
    """Utility function to optimize static assets for production"""
    optimizer = get_cdn_optimizer()
    
    # Generate asset manifest
    manifest = optimizer.generate_asset_manifest()
    
    # Get optimization config
    config = optimizer.get_optimization_config()
    
    logging.info("Static asset optimization completed")
    logging.info(f"Asset manifest: {len(manifest)} files")
    logging.info(f"CDN enabled: {optimizer.cdn_config['enabled']}")
    
    return {
        "manifest": manifest,
        "config": config,
        "cdn_stats": optimizer.get_cdn_stats()
    }
