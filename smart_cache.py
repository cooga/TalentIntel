"""
Smart Cache Manager
智能缓存管理器 - 基于 Crawl4AI 的分层缓存策略

三层缓存架构:
L1: 内存缓存 (热数据，最快速)
L2: 磁盘缓存 (近期访问，持久化)
L3: 浏览器缓存 (已渲染页面复用)
"""

import hashlib
import json
import pickle
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import asyncio
from functools import wraps


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat()
        }


class MemoryCache:
    """
    L1 内存缓存
    
    特点:
    - 最快访问速度
    - 自动过期清理
    - LRU淘汰策略
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大条目数
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            # 更新访问统计
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            return entry.data
    
    def set(self, key: str, data: Any, ttl: int = None):
        """设置缓存"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # LRU淘汰
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl)
            )
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def _evict_lru(self):
        """LRU淘汰最少使用"""
        if not self._cache:
            return
        
        # 找出最少访问且最早的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].access_count, self._cache[k].last_accessed)
        )
        del self._cache[lru_key]
    
    def _cleanup_loop(self):
        """后台清理过期条目"""
        while True:
            time.sleep(60)  # 每分钟清理一次
            self._cleanup_expired()
    
    def _cleanup_expired(self):
        """清理过期条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
    
    def stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for e in self._cache.values() if e.is_expired())
            return {
                "total_entries": total,
                "expired_entries": expired,
                "valid_entries": total - expired,
                "max_size": self.max_size
            }


class DiskCache:
    """
    L2 磁盘缓存
    
    特点:
    - 持久化存储
    - 进程间共享
    - 大容量
    """
    
    def __init__(self, cache_dir: str = "~/.talentintel/cache", 
                 default_ttl: int = 86400):
        """
        初始化磁盘缓存
        
        Args:
            cache_dir: 缓存目录
            default_ttl: 默认过期时间（秒）
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._metadata_file = self.cache_dir / "_metadata.json"
        self._metadata: Dict[str, Dict] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """加载元数据"""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r') as f:
                    self._metadata = json.load(f)
            except:
                self._metadata = {}
    
    def _save_metadata(self):
        """保存元数据"""
        with open(self._metadata_file, 'w') as f:
            json.dump(self._metadata, f, indent=2)
    
    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希避免文件名过长
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        meta = self._metadata.get(key)
        if meta is None:
            return None
        
        # 检查过期
        expires_at = datetime.fromisoformat(meta["expires_at"])
        if datetime.now() > expires_at:
            self.delete(key)
            return None
        
        # 读取数据
        cache_file = self._get_cache_file(key)
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # 更新访问统计
            meta["access_count"] = meta.get("access_count", 0) + 1
            meta["last_accessed"] = datetime.now().isoformat()
            self._save_metadata()
            
            return data
        except:
            return None
    
    def set(self, key: str, data: Any, ttl: int = None):
        """设置缓存"""
        if ttl is None:
            ttl = self.default_ttl
        
        cache_file = self._get_cache_file(key)
        
        try:
            # 保存数据
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # 更新元数据
            self._metadata[key] = {
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                "access_count": 0,
                "last_accessed": datetime.now().isoformat()
            }
            self._save_metadata()
        except Exception as e:
            print(f"Failed to write cache: {e}")
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._metadata:
            del self._metadata[key]
            self._save_metadata()
        
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False
    
    def clear(self):
        """清空缓存"""
        # 删除所有缓存文件
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
        
        self._metadata.clear()
        self._save_metadata()
    
    def cleanup_expired(self):
        """清理过期缓存"""
        expired_keys = []
        
        for key, meta in self._metadata.items():
            expires_at = datetime.fromisoformat(meta["expires_at"])
            if datetime.now() > expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
        
        return len(expired_keys)
    
    def stats(self) -> Dict:
        """获取统计信息"""
        total_size = sum(
            f.stat().st_size 
            for f in self.cache_dir.glob("*.cache")
        )
        
        return {
            "total_entries": len(self._metadata),
            "cache_dir": str(self.cache_dir),
            "total_size_mb": total_size / (1024 * 1024)
        }


class SmartCacheManager:
    """
    智能缓存管理器
    
    三层缓存协调:
    L1: MemoryCache (热数据)
    L2: DiskCache (近期数据)
    L3: Browser Cache (已渲染页面)
    """
    
    def __init__(self, 
                 memory_cache_size: int = 1000,
                 disk_cache_dir: str = "~/.talentintel/cache"):
        self.l1_memory = MemoryCache(max_size=memory_cache_size)
        self.l2_disk = DiskCache(cache_dir=disk_cache_dir)
        self._browser_cache: Dict[str, Any] = {}  # L3 浏览器缓存
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存（L1 -> L2 -> L3）
        
        Args:
            key: 缓存键
            
        Returns:
            缓存数据或None
        """
        # L1: 内存缓存
        data = self.l1_memory.get(key)
        if data is not None:
            return data
        
        # L2: 磁盘缓存
        data = self.l2_disk.get(key)
        if data is not None:
            # 回填L1
            self.l1_memory.set(key, data)
            return data
        
        # L3: 浏览器缓存（仅检查存在性，不自动回填）
        if key in self._browser_cache:
            return self._browser_cache[key]
        
        return None
    
    def set(self, key: str, data: Any, ttl: int = 3600, 
            cache_level: str = "all"):
        """
        设置缓存
        
        Args:
            key: 缓存键
            data: 数据
            ttl: 过期时间
            cache_level: "memory", "disk", "all"
        """
        if cache_level in ("memory", "all"):
            self.l1_memory.set(key, data, ttl)
        
        if cache_level in ("disk", "all"):
            self.l2_disk.set(key, data, ttl)
    
    def set_browser_cache(self, key: str, page_data: Any):
        """设置浏览器缓存（L3）"""
        self._browser_cache[key] = page_data
    
    def get_browser_cache(self, key: str) -> Optional[Any]:
        """获取浏览器缓存"""
        return self._browser_cache.get(key)
    
    def invalidate(self, key: str):
        """使缓存失效"""
        self.l1_memory.delete(key)
        self.l2_disk.delete(key)
        if key in self._browser_cache:
            del self._browser_cache[key]
    
    def clear_all(self):
        """清空所有缓存"""
        self.l1_memory.clear()
        self.l2_disk.clear()
        self._browser_cache.clear()
    
    def stats(self) -> Dict:
        """获取统计信息"""
        return {
            "l1_memory": self.l1_memory.stats(),
            "l2_disk": self.l2_disk.stats(),
            "l3_browser": {
                "total_entries": len(self._browser_cache)
            }
        }


# 装饰器：自动缓存
def cached(cache_manager: SmartCacheManager, ttl: int = 3600, 
           key_func: Callable = None):
    """
    缓存装饰器
    
    用法:
        @cached(cache, ttl=3600)
        async def fetch_data(url):
            return await crawler.crawl(url)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # 尝试获取缓存
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return async_wrapper
    return decorator


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("Smart Cache Manager Test")
    print("=" * 60)
    
    cache = SmartCacheManager()
    
    # 测试 L1 内存缓存
    print("\n1. L1 Memory Cache:")
    cache.l1_memory.set("key1", {"data": "test1"}, ttl=60)
    print(f"   Set key1")
    print(f"   Get key1: {cache.l1_memory.get('key1')}")
    print(f"   Stats: {cache.l1_memory.stats()}")
    
    # 测试 L2 磁盘缓存
    print("\n2. L2 Disk Cache:")
    cache.l2_disk.set("key2", {"data": "test2"}, ttl=3600)
    print(f"   Set key2")
    print(f"   Get key2: {cache.l2_disk.get('key2')}")
    print(f"   Stats: {cache.l2_disk.stats()}")
    
    # 测试分层获取
    print("\n3. Tiered Cache Get:")
    cache.l2_disk.set("key3", {"source": "disk"}, ttl=3600)
    result = cache.get("key3")  # 应从L2读取并回填L1
    print(f"   Result: {result}")
    print(f"   L1 has key3: {cache.l1_memory.get('key3') is not None}")
    
    # 测试统计
    print("\n4. Overall Stats:")
    print(f"   {cache.stats()}")
    
    # 清理
    cache.clear_all()
    
    print("\n" + "=" * 60)
    print("Cache Test Completed!")
    print("=" * 60)
