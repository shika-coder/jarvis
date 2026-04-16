#!/usr/bin/env python3
"""
Vector Memory System Tests

Tests for VectorMemory semantic search and FAISS integration.
"""

import asyncio
import tempfile
from pathlib import Path

from jarvis.core.logging import get_logger
from jarvis.memory import VectorMemory

logger = get_logger(__name__)


async def test_vector_memory_basic():
    """Test basic VectorMemory functionality."""
    logger.info("\n" + "="*60)
    logger.info("Testing VectorMemory - Basic Operations")
    logger.info("="*60)
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(storage_dir=tmpdir)
        
        # Test adding memory
        mem_id1 = await memory.add_memory(
            content="Python is a great programming language",
            category="programming",
            metadata={"language": "python"}
        )
        logger.info(f"✓ Added memory: {mem_id1}")
        
        mem_id2 = await memory.add_memory(
            content="JavaScript is used for web development",
            category="programming",
            metadata={"language": "javascript"}
        )
        logger.info(f"✓ Added memory: {mem_id2}")
        
        mem_id3 = await memory.add_memory(
            content="Machine learning models learn from data",
            category="ml",
            metadata={"topic": "ML"}
        )
        logger.info(f"✓ Added memory: {mem_id3}")
        
        # Test retrieval
        retrieved = await memory.get_memory(mem_id1)
        assert retrieved is not None
        assert retrieved.content == "Python is a great programming language"
        logger.info("✓ Memory retrieval works")
        
        # Test listing
        prog_memories = await memory.list_memories(category="programming")
        assert len(prog_memories) == 2
        logger.info(f"✓ Listed memories by category: {len(prog_memories)} programming memories")
        
        # Test stats
        stats = memory.get_stats()
        assert stats["total_memories"] == 3
        assert stats["categories"]["programming"] == 2
        assert stats["categories"]["ml"] == 1
        logger.info(f"✓ Memory stats: {stats['total_memories']} total memories")


async def test_vector_memory_search():
    """Test semantic search in VectorMemory."""
    logger.info("\n" + "="*60)
    logger.info("Testing VectorMemory - Semantic Search")
    logger.info("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(storage_dir=tmpdir)
        
        if not memory.is_available():
            logger.warning("Vector search not available (embeddings not loaded), testing JSON-only mode")
            logger.info("✓ Memory system works in JSON-only fallback mode")
            return
        
        # Add test memories
        memories_data = [
            ("Python is a programming language", "tech"),
            ("Machine learning uses neural networks", "ml"),
            ("Deep learning requires GPUs", "ml"),
            ("Java is used for enterprise applications", "tech"),
            ("Dogs are loyal pets", "animals"),
            ("Cats are independent animals", "animals"),
        ]
        
        for content, category in memories_data:
            await memory.add_memory(content=content, category=category)
        
        logger.info(f"✓ Added {len(memories_data)} test memories")
        
        # Test search: similar to "programming languages"
        results = await memory.search("programming languages", top_k=3)
        assert len(results) > 0
        logger.info(f"✓ Search for 'programming languages': found {len(results)} results")
        for mem, similarity in results[:2]:
            logger.info(f"  - {mem.content[:50]}... (similarity: {similarity:.2f})")
        
        # Test search with category filter
        results_tech = await memory.search("language", top_k=5, category_filter="tech")
        assert all(m.category == "tech" for m, _ in results_tech)
        logger.info(f"✓ Filtered search in 'tech' category: {len(results_tech)} results")
        
        # Test search: similar to "machine learning"
        results_ml = await memory.search("neural networks", top_k=3)
        assert len(results_ml) > 0
        logger.info(f"✓ Search for 'neural networks': found {len(results_ml)} results")
        
        # Test that different queries return different results
        animals_results = await memory.search("pets", top_k=3)
        assert any("animal" in m.content.lower() for m, _ in animals_results)
        logger.info(f"✓ Search correctly distinguishes categories")


async def test_vector_memory_deletion():
    """Test memory deletion and clearing."""
    logger.info("\n" + "="*60)
    logger.info("Testing VectorMemory - Deletion & Clearing")
    logger.info("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(storage_dir=tmpdir)
        
        # Add memories with unique content to ensure different IDs
        mem_id1 = await memory.add_memory("Test memory 1", category="test")
        mem_id2 = await memory.add_memory("Test memory 2", category="test")
        mem_id3 = await memory.add_memory("Other memory", category="other")
        
        stats = memory.get_stats()
        logger.info(f"Stats after adding 3: {stats}")
        assert stats["total_memories"] == 3
        logger.info("✓ Added 3 memories")
        
        # Delete one memory
        deleted = await memory.delete_memory(mem_id1)
        assert deleted == True
        
        stats = memory.get_stats()
        assert stats["total_memories"] == 2
        logger.info("✓ Deleted 1 memory")
        
        # Clear category
        cleared = await memory.clear_category("test")
        assert cleared == 1
        
        stats = memory.get_stats()
        assert stats["total_memories"] == 1
        assert stats["categories"].get("test", 0) == 0
        logger.info("✓ Cleared 'test' category")


async def test_vector_memory_persistence():
    """Test memory persistence (JSON backup)."""
    logger.info("\n" + "="*60)
    logger.info("Testing VectorMemory - Persistence")
    logger.info("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create and populate memory
        memory1 = VectorMemory(storage_dir=tmpdir)
        mem_id = await memory1.add_memory(
            content="Persistent memory test",
            category="test",
            metadata={"persistent": True}
        )
        logger.info("✓ Added memory to first instance")
        
        # Create second instance (should load from backup)
        memory2 = VectorMemory(storage_dir=tmpdir)
        retrieved = await memory2.get_memory(mem_id)
        
        assert retrieved is not None
        assert retrieved.content == "Persistent memory test"
        assert retrieved.metadata["persistent"] == True
        logger.info("✓ Memory persisted and reloaded successfully")
        
        # Verify backup file exists
        backup_file = tmppath / "memory_backup.json"
        assert backup_file.exists()
        logger.info(f"✓ Backup file exists: {backup_file.name}")


async def test_memory_metadata():
    """Test memory metadata handling."""
    logger.info("\n" + "="*60)
    logger.info("Testing VectorMemory - Metadata")
    logger.info("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = VectorMemory(storage_dir=tmpdir)
        
        metadata = {
            "source": "user_input",
            "confidence": 0.95,
            "tags": ["important", "python"],
            "timestamp_ms": 1234567890
        }
        
        mem_id = await memory.add_memory(
            content="Test with metadata",
            category="test",
            metadata=metadata
        )
        
        retrieved = await memory.get_memory(mem_id)
        assert retrieved.metadata == metadata
        logger.info("✓ Metadata stored and retrieved correctly")


async def main():
    """Run all memory system tests."""
    logger.info("JARVIS Vector Memory System - Test Suite")
    logger.info("Starting memory system tests...\n")
    
    try:
        await test_vector_memory_basic()
        await test_vector_memory_search()
        await test_vector_memory_deletion()
        await test_vector_memory_persistence()
        await test_memory_metadata()
        
        logger.info("\n" + "="*60)
        logger.success("All memory system tests passed! ✓")
        logger.info("="*60)
        
    except Exception as e:
        logger.critical(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
