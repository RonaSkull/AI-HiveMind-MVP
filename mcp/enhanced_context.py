"""
Enhanced context management for agents with support for:
- Hierarchical context
- Conversation history
- Metadata and tags
- Context relationships
- Versioning
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, AsyncGenerator, cast

logger = logging.getLogger(__name__)

class ContextNode:
    """Represents a node in the context hierarchy."""
    
    def __init__(
        self,
        node_id: str,
        data: Dict[str, Any],
        node_type: str = "generic",
        parent_id: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.data = data
        self.node_type = node_type
        self.parent_id = parent_id
        self.tags = tags or set()
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.version = 1
        
    def update(self, data: Dict[str, Any]) -> None:
        """Update the node's data and increment version."""
        self.data.update(data)
        self.updated_at = datetime.utcnow()
        self.version += 1
        
    def add_tag(self, tag: str) -> None:
        """Add a tag to the node."""
        self.tags.add(tag)
        self.updated_at = datetime.utcnow()
        
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the node."""
        self.tags.discard(tag)
        self.updated_at = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "parent_id": self.parent_id,
            "data": self.data,
            "tags": list(self.tags),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextNode':
        """Create a ContextNode from a dictionary."""
        node = cls(
            node_id=data["node_id"],
            data=data["data"],
            node_type=data.get("node_type", "generic"),
            parent_id=data.get("parent_id"),
            tags=set(data.get("tags", [])),
            metadata=data.get("metadata", {})
        )
        node.created_at = datetime.fromisoformat(data["created_at"])
        node.updated_at = datetime.fromisoformat(data["updated_at"])
        node.version = data.get("version", 1)
        return node


class EnhancedContextManager:
    """
    Enhanced context manager with support for hierarchical contexts,
    relationships, and metadata.
    """
    
    def __init__(self, storage_backend: Any):
        """
        Initialize the context manager with a storage backend.
        
        Args:
            storage_backend: Storage backend that implements async methods:
                          - get(key: str) -> Any
                          - set(key: str, value: Any, **kwargs) -> bool
                          - delete(key: str) -> bool
                          - exists(key: str) -> bool
        """
        self.storage = storage_backend
        self._lock = asyncio.Lock()
        
        # Verify required methods exist
        required_methods = ['get', 'set', 'delete', 'exists']
        for method in required_methods:
            if not hasattr(self.storage, method) or not callable(getattr(self.storage, method)):
                raise ValueError(f"Storage backend must implement '{method}' method")
        
    def _generate_id(self) -> str:
        """Generate a unique ID for new context nodes."""
        return f"ctx_{uuid.uuid4().hex}"
    
    async def create_context(
        self,
        data: Dict[str, Any],
        context_type: str = "generic",
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Create a new context node.
        
        Args:
            data: The context data to store
            context_type: Type of context (e.g., 'conversation', 'task', 'user')
            parent_id: Optional parent context ID
            tags: Optional list of tags for the context
            metadata: Optional metadata dictionary
            ttl: Optional time-to-live in seconds
            
        Returns:
            str: The ID of the created context
        """
        node_id = self._generate_id()
        node = ContextNode(
            node_id=node_id,
            data=data,
            node_type=context_type,
            parent_id=parent_id,
            tags=set(tags or []),
            metadata=metadata or {}
        )
        
        # Store the node
        await self.set(node_id, node.to_dict(), ttl=ttl)
        
        # If there's a parent, create the relationship
        if parent_id:
            await self._add_relationship(parent_id, node_id)
            
        return node_id
        
    async def _add_child_to_parent(self, parent_id: str, child_id: str) -> None:
        """Add a child context ID to a parent's children list."""
        try:
            # Get parent context
            parent = await self.get_context(parent_id)
            if not parent:
                logger.warning(f"Parent context {parent_id} not found")
                return
                
            # Initialize children if not exists
            if "children" not in parent:
                parent["children"] = []
                
            # Add child if not already in the list
            if child_id not in parent["children"]:
                parent["children"].append(child_id)
                # Save the updated parent
                await self.set(parent_id, parent)
        except Exception as e:
            logger.error(f"Failed to add relationship {parent_id} -> {child_id}: {e}")
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by ID.
        
        Args:
            context_id: The ID of the context to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The context data if found, None otherwise
        """
        try:
            data = await self.storage.get(context_id)
            if not data:
                return None
                
            if isinstance(data, dict):
                return data
                
            if isinstance(data, str):
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse context data for {context_id}")
                    return None
                    
            return None
        except Exception as e:
            logger.error(f"Error getting context {context_id}: {e}")
            return None
    
    async def update_context(
        self,
        context_id: str,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Update an existing context.
        
        Args:
            context_id: The ID of the context to update
            data: New data to merge with existing data
            tags: New tags to add to existing tags
            metadata: New metadata to merge with existing metadata
            ttl: Optional time-to-live in seconds
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        async with self._lock:
            # Get existing context
            existing = await self.get_context(context_id)
            if not existing:
                return False
                
            # Update data if provided
            if data is not None:
                if 'data' in existing and isinstance(existing['data'], dict):
                    existing['data'].update(data)
                else:
                    existing['data'] = data
            
            # Update tags if provided
            if tags:
                existing_tags = set(existing.get('tags', []))
                existing_tags.update(tags)
                existing['tags'] = list(existing_tags)
            
            # Update metadata if provided
            if metadata is not None:
                if 'metadata' in existing and isinstance(existing['metadata'], dict):
                    existing['metadata'].update(metadata)
                else:
                    existing['metadata'] = metadata
            
            # Update timestamps
            existing['updated_at'] = datetime.utcnow().isoformat()
            
            # Increment version
            existing['version'] = existing.get('version', 0) + 1
            
            # Save back to storage
            return await self.set(context_id, existing, ttl=ttl)
            
        # Get the existing context
        existing = await self.get_context(context_id)
        if not existing:
            return False
            
        # Update data if provided
        if data is not None:
            if 'data' in existing and isinstance(existing['data'], dict):
                existing['data'].update(data)
            else:
                existing['data'] = data
                
        # Update tags if provided
        if tags is not None:
            if 'tags' in existing and isinstance(existing['tags'], list):
                existing['tags'].extend(tag for tag in tags if tag not in existing['tags'])
            else:
                existing['tags'] = list(set(tags))  # Remove duplicates
                
        # Update metadata if provided
        if metadata is not None:
            if 'metadata' in existing and isinstance(existing['metadata'], dict):
                existing['metadata'].update(metadata)
            else:
                existing['metadata'] = metadata
                
        # Update timestamps and version
        existing['updated_at'] = datetime.utcnow().isoformat()
        existing['version'] = existing.get('version', 0) + 1
        
        # Save back to storage
        return await self.set(context_id, existing, ttl=ttl)

    async def add_context_tag(self, context_id: str, tag: str) -> bool:
        """
        Add a tag to a context.
        
        Args:
            context_id: The ID of the context
            tag: The tag to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the existing context
            existing = await self.get_context(context_id)
            if not existing:
                return False
                
            # Initialize tags if not exists
            if 'tags' not in existing or not isinstance(existing['tags'], list):
                existing['tags'] = []
                
            # Add tag if not already present
            if tag not in existing['tags']:
                existing['tags'].append(tag)
                
            # Update the context
            return await self.update_context(
                context_id,
                tags=existing['tags']
            )
            
        except Exception as e:
            logger.error(f"Error adding tag to context {context_id}: {e}")
            return False
            return True
            
        except Exception as e:
            logger.error(f"Error adding tag to context {context_id}: {e}")
            return False
    
    async def find_contexts_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Find all contexts with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of matching context dictionaries
        """
        results = []
        try:
            if self._use_redis:
                # Note: This is inefficient for Redis - in production, use Redis sets or search
                cursor = '0'
                while cursor != 0:
                    cursor, keys = await self.storage.scan(
                        cursor=cursor,
                        match='context:*',
                        count=100
                    )
                    for key in keys:
                        data = await self.storage.get(key)
                        if data:
                            node = ContextNode.from_dict(json.loads(data))
                            if tag in node.tags:
                                results.append(node.to_dict())
            else:
                for key, data in self.storage.items():
                    if key.startswith('context:'):
                        node = ContextNode.from_dict(data)
                        if tag in node.tags:
                            results.append(node.to_dict())
                            
        except Exception as e:
            logger.error(f"Error finding contexts by tag {tag}: {e}")
            
        return results
