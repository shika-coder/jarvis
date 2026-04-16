"""
Vector-based memory system using FAISS.

Provides semantic memory storage and retrieval using embeddings.
"""

import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import numpy as np

from jarvis.core.logging import get_logger

logger = get_logger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed. Install with: pip install faiss-cpu")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")


@dataclass
class Memory:
    """Represents a single memory item."""
    id: str
    content: str
    category: str
    timestamp: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for JSON serialization)."""
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class VectorMemory:
    """
    Vector-based memory system using FAISS for semantic search.
    
    Stores memories with embeddings and enables semantic similarity search.
    Falls back to JSON for compatibility if FAISS unavailable.
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        storage_dir: str = "memory",
        index_file: str = "faiss_index.bin",
        backup_file: str = "memory_backup.json",
        dimension: int = 384
    ):
        """
        Initialize VectorMemory.
        
        Args:
            embedding_model: Sentence transformer model name
            storage_dir: Directory to store FAISS index and backups
            index_file: FAISS index filename
            backup_file: JSON backup filename
            dimension: Embedding dimension (depends on model)
        """
        self.embedding_model_name = embedding_model
        self.storage_dir = Path(storage_dir)
        self.index_file = self.storage_dir / index_file
        self.backup_file = self.storage_dir / backup_file
        self.dimension = dimension
        
        # Create storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = None
        self.index = None
        self.id_to_memory: Dict[str, Memory] = {}
        
        if EMBEDDINGS_AVAILABLE and FAISS_AVAILABLE:
            self._init_embeddings()
            self._load_or_create_index()
        else:
            if not EMBEDDINGS_AVAILABLE:
                logger.warning("Sentence transformers not available, using JSON-only mode")
            if not FAISS_AVAILABLE:
                logger.warning("FAISS not available, using JSON-only mode")
            self._load_backup()
    
    def _init_embeddings(self) -> None:
        """Load embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
    
    def _load_or_create_index(self) -> None:
        """Load existing FAISS index or create new one."""
        try:
            if self.index_file.exists():
                logger.info(f"Loading FAISS index from {self.index_file}")
                self.index = faiss.read_index(str(self.index_file))
                logger.info(f"Index loaded: {self.index.ntotal} items")
            else:
                logger.info(f"Creating new FAISS index (dimension: {self.dimension})")
                self.index = faiss.IndexFlatL2(self.dimension)
            
            # Load memory backup
            self._load_backup()
        except Exception as e:
            logger.error(f"Failed to load/create FAISS index: {e}")
            self.index = None
    
    def _load_backup(self) -> None:
        """Load memory from JSON backup."""
        if self.backup_file.exists():
            try:
                logger.info(f"Loading memory backup from {self.backup_file}")
                with open(self.backup_file, "r") as f:
                    data = json.load(f)
                
                for mem_dict in data:
                    mem = Memory(
                        id=mem_dict["id"],
                        content=mem_dict["content"],
                        category=mem_dict["category"],
                        timestamp=mem_dict["timestamp"],
                        metadata=mem_dict.get("metadata", {}),
                    )
                    self.id_to_memory[mem.id] = mem
                
                logger.info(f"Loaded {len(self.id_to_memory)} memories from backup")
            except Exception as e:
                logger.error(f"Failed to load backup: {e}")
    
    def _save_backup(self) -> None:
        """Save memories to JSON backup."""
        try:
            data = [mem.to_dict() for mem in self.id_to_memory.values()]
            with open(self.backup_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(data)} memories to backup")
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
    
    def _encode(self, text: str) -> Optional[np.ndarray]:
        """Encode text to embedding."""
        if self.embedding_model is None:
            return None
        
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.astype("float32")
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return None
    
    async def add_memory(
        self,
        content: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """
        Add a memory to the system.
        
        Args:
            content: Memory content
            category: Memory category (e.g., "project", "preference", "conversation")
            metadata: Additional metadata
            memory_id: Optional custom ID
        
        Returns:
            Memory ID
        """
        memory_id = memory_id or f"{category}_{int(time.time() * 1000)}"
        
        memory = Memory(
            id=memory_id,
            content=content,
            category=category,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        # Generate embedding if available
        if self.embedding_model:
            embedding = self._encode(content)
            if embedding is not None:
                memory.embedding = embedding.tolist()
                
                # Add to FAISS index
                if self.index is not None:
                    try:
                        self.index.add(embedding.reshape(1, -1))
                        logger.debug(f"Added embedding to FAISS index")
                    except Exception as e:
                        logger.error(f"Failed to add to FAISS index: {e}")
        
        # Store in memory map
        self.id_to_memory[memory_id] = memory
        
        # Save backup
        self._save_backup()
        
        # Persist FAISS index
        if self.index:
            try:
                faiss.write_index(self.index, str(self.index_file))
            except Exception as e:
                logger.error(f"Failed to save FAISS index: {e}")
        
        logger.info(f"Memory added: {memory_id}")
        return memory_id
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Tuple[Memory, float]]:
        """
        Search for similar memories.
        
        Args:
            query: Query text
            top_k: Number of results to return
            category_filter: Optional category filter
        
        Returns:
            List of (Memory, similarity_score) tuples
        """
        if not self.embedding_model or not self.index:
            logger.warning("Cannot perform semantic search without embeddings/index")
            return []
        
        try:
            # Encode query
            query_embedding = self._encode(query)
            if query_embedding is None:
                return []
            
            # Search FAISS index
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                min(top_k * 2, self.index.ntotal)  # Get extra to filter
            )
            
            results = []
            memory_list = list(self.id_to_memory.values())
            
            for idx, distance in zip(indices[0], distances[0]):
                if idx >= len(memory_list):
                    continue
                
                memory = memory_list[idx]
                
                # Filter by category if specified
                if category_filter and memory.category != category_filter:
                    continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity = 1.0 / (1.0 + distance)
                results.append((memory, similarity))
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"Found {len(results)} similar memories")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a specific memory by ID."""
        return self.id_to_memory.get(memory_id)
    
    async def list_memories(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Memory]:
        """
        List memories, optionally filtered by category.
        
        Args:
            category: Optional category filter
            limit: Maximum number of results
        
        Returns:
            List of memories
        """
        memories = list(self.id_to_memory.values())
        
        if category:
            memories = [m for m in memories if m.category == category]
        
        # Sort by timestamp (newest first)
        memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        return memories[:limit]
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        if memory_id in self.id_to_memory:
            del self.id_to_memory[memory_id]
            self._save_backup()
            logger.info(f"Memory deleted: {memory_id}")
            return True
        return False
    
    async def clear_category(self, category: str) -> int:
        """Clear all memories in a category."""
        to_delete = [m.id for m in self.id_to_memory.values() if m.category == category]
        for mem_id in to_delete:
            await self.delete_memory(mem_id)
        logger.info(f"Cleared {len(to_delete)} memories from category: {category}")
        return len(to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        categories = {}
        for memory in self.id_to_memory.values():
            if memory.category not in categories:
                categories[memory.category] = 0
            categories[memory.category] += 1
        
        return {
            "total_memories": len(self.id_to_memory),
            "index_size": self.index.ntotal if self.index else 0,
            "categories": categories,
            "embedding_model": self.embedding_model_name if self.embedding_model else None,
            "has_faiss": self.index is not None,
        }
    
    def is_available(self) -> bool:
        """Check if vector memory is available."""
        return self.embedding_model is not None and self.index is not None
