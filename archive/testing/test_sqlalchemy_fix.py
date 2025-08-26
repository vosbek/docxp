"""
Test script to verify the SQLAlchemy metadata reserved word fix.
This script demonstrates that the fix resolves the original error.
"""

import asyncio
from app.core.database import CodeEntity, Base, engine, init_db


async def test_sqlalchemy_fix():
    """Test that the SQLAlchemy reserved word issue is resolved."""
    
    print("=" * 60)
    print("Testing SQLAlchemy Reserved Word Fix")
    print("=" * 60)
    
    # Test 1: Verify we can import and create models without errors
    print("\n✓ Test 1: Model import and creation")
    try:
        entity = CodeEntity(
            id='test_entity_123',
            name='TestClass',
            type='class',
            file_path='/app/models/test.py',
            module_path='app.models.test',
            line_number=10,
            docstring='A test class for demonstration',
            language='python',
            visibility='public',
            is_abstract=False,
            design_patterns=['Factory', 'Singleton'],
            entity_metadata={
                'complexity_score': 5,
                'dependencies': ['logging', 'typing'],
                'module_path': 'app.models.test',
                'author': 'Development Team'
            }
        )
        print(f"   CodeEntity created successfully!")
        print(f"   Entity ID: {entity.id}")
        print(f"   Entity metadata: {entity.entity_metadata}")
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    # Test 2: Verify SQLAlchemy's built-in metadata is still accessible
    print("\n✓ Test 2: SQLAlchemy built-in metadata accessibility")
    try:
        metadata = Base.metadata
        print(f"   SQLAlchemy metadata object: {type(metadata)}")
        print(f"   Number of tables defined: {len(metadata.tables)}")
        
        # List all table names
        table_names = list(metadata.tables.keys())
        print(f"   Tables: {', '.join(table_names)}")
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    # Test 3: Verify database schema creation works
    print("\n✓ Test 3: Database schema creation")
    try:
        # This would have failed with the original 'metadata' column name
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   Database schema created successfully!")
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    # Test 4: Verify entity_metadata column functionality
    print("\n✓ Test 4: entity_metadata column functionality")
    try:
        # Test that we can access and modify the entity_metadata field
        entity.entity_metadata['new_field'] = 'new_value'
        entity.entity_metadata.update({
            'performance_metrics': {'execution_time': 0.5, 'memory_usage': '10MB'},
            'testing_status': 'fully_tested'
        })
        
        print(f"   Updated metadata: {entity.entity_metadata}")
        print(f"   Metadata keys: {list(entity.entity_metadata.keys())}")
        
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("The SQLAlchemy reserved word conflict has been successfully resolved.")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_sqlalchemy_fix())
    exit(0 if success else 1)