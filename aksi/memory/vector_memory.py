"""
Vector Memory Module
====================

ChromaDB-based vector memory for AKSI agent.
Provides semantic search and long-term memory capabilities.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from aksi.config import settings

# Lazy import for chromadb
_chromadb = None


def _get_chromadb():
    """Lazy import chromadb."""
    global _chromadb
    if _chromadb is None:
        try:
            import chromadb
            from chromadb.config import Settings
            _chromadb = (chromadb, Settings)
        except ImportError:
            _chromadb = (None, None)
    return _chromadb


class VectorMemory:
    """
    Vector-based memory using ChromaDB.

    Provides:
    - Semantic search over stored memories
    - Automatic embedding generation
    - Persistence across sessions
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize vector memory.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory or settings.chromadb_persist_directory
        self.collection_name = collection_name or settings.chromadb_collection_name
        self._client = None
        self._collection = None
        self._initialized = False

    def _ensure_initialized(self):
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return True

        chromadb, Settings = _get_chromadb()

        if chromadb is None:
            return False

        try:
            # Create persistent client
            self._client = chromadb.Client(Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            self._initialized = True
            return True
        except Exception:
            return False

    async def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store content in vector memory.

        Args:
            content: Text content to store
            metadata: Additional metadata
            memory_id: Optional custom ID (auto-generated if not provided)

        Returns:
            Memory ID if successful, None otherwise
        """
        if not self._ensure_initialized():
            return None

        # Generate ID if not provided
        if memory_id is None:
            memory_id = hashlib.sha256(
                f"{content}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]

        # Build metadata
        full_metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "content_length": len(content),
            **(metadata or {})
        }

        try:
            self._collection.add(
                documents=[content],
                metadatas=[full_metadata],
                ids=[memory_id]
            )
            return memory_id
        except Exception:
            return None

    async def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories by semantic similarity.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching memories with scores
        """
        if not self._ensure_initialized():
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )

            memories = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    memory = {
                        "id": results["ids"][0][i] if results["ids"] else None,
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results.get("distances") else None
                    }
                    memories.append(memory)

            return memories
        except Exception:
            return []

    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            Memory dict if found, None otherwise
        """
        if not self._ensure_initialized():
            return None

        try:
            result = self._collection.get(ids=[memory_id])

            if result and result["documents"] and result["documents"][0]:
                return {
                    "id": memory_id,
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {}
                }
            return None
        except Exception:
            return None

    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if deleted successfully
        """
        if not self._ensure_initialized():
            return False

        try:
            self._collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing memory.

        Args:
            memory_id: ID of the memory to update
            content: New content (optional)
            metadata: New metadata (optional)

        Returns:
            True if updated successfully
        """
        if not self._ensure_initialized():
            return False

        try:
            update_kwargs = {"ids": [memory_id]}

            if content:
                update_kwargs["documents"] = [content]

            if metadata:
                # Merge with existing metadata
                existing = await self.get(memory_id)
                if existing:
                    merged_metadata = {
                        **existing.get("metadata", {}),
                        **metadata,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    update_kwargs["metadatas"] = [merged_metadata]

            self._collection.update(**update_kwargs)
            return True
        except Exception:
            return False

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all memories.

        Args:
            limit: Maximum number of memories to return
            offset: Number of memories to skip

        Returns:
            List of all memories
        """
        if not self._ensure_initialized():
            return []

        try:
            result = self._collection.get(
                limit=limit,
                offset=offset
            )

            memories = []
            if result and result["documents"]:
                for i, doc in enumerate(result["documents"]):
                    memory = {
                        "id": result["ids"][i] if result["ids"] else None,
                        "content": doc,
                        "metadata": result["metadatas"][i] if result["metadatas"] else {}
                    }
                    memories.append(memory)

            return memories
        except Exception:
            return []

    async def count(self) -> int:
        """
        Get total number of memories.

        Returns:
            Count of memories in collection
        """
        if not self._ensure_initialized():
            return 0

        try:
            return self._collection.count()
        except Exception:
            return 0

    async def clear(self) -> bool:
        """
        Clear all memories from the collection.

        Returns:
            True if cleared successfully
        """
        if not self._ensure_initialized():
            return False

        try:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        """Check if ChromaDB is available."""
        chromadb, _ = _get_chromadb()
        return chromadb is not None
