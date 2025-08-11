#!/usr/bin/env python3
"""
Comprehensive test of the improved chunking strategy.
"""

def test_large_file_chunking():
    """Test chunking with a large file that will be split into multiple chunks."""
    
    # Read the large test file
    with open('test_large_file.py', 'r') as f:
        large_code = f.read()
    
    print("🧪 Testing Comprehensive Chunking Strategy")
    print("=" * 60)
    print(f"📁 Large file size: {len(large_code)/1024:.1f}KB")
    
    try:
        from genai_uplifter_simplified import (
            split_code_into_api_chunks, 
            ensure_imports_in_first_chunk,
            validate_reassembled_code,
            reassemble_chunks_intelligently
        )
        
        print("✅ Successfully imported chunking functions")
        
        # Test chunking
        print("\n📦 Testing code chunking...")
        chunks = split_code_into_api_chunks(large_code)
        
        print(f"📊 Split into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            size_kb = len(chunk['code']) / 1024
            complete = chunk.get('complete_structures', False)
            print(f"  Chunk {i+1}: {size_kb:.1f}KB, Complete: {complete}")
        
        # Test import preservation
        print("\n🔧 Testing import preservation...")
        chunks_with_imports = ensure_imports_in_first_chunk(chunks)
        
        # Check imports in first chunk
        first_chunk = chunks_with_imports[0]['code']
        import_lines = [line for line in first_chunk.split('\n') if line.strip().startswith(('import ', 'from '))]
        print(f"📦 Imports in first chunk: {len(import_lines)}")
        for imp in import_lines:
            print(f"  {imp.strip()}")
        
        # Show chunk boundaries
        print("\n🔍 Chunk boundaries analysis:")
        for i, chunk in enumerate(chunks):
            lines = chunk['code'].split('\n')
            print(f"\nChunk {i+1} ({len(lines)} lines):")
            
            # Show first few lines
            print("  Start:")
            for j, line in enumerate(lines[:3]):
                print(f"    {j+1:2d}: {line[:60]}{'...' if len(line) > 60 else ''}")
            
            # Show last few lines
            print("  End:")
            for j, line in enumerate(lines[-3:]):
                actual_line_num = len(lines) - 3 + j
                print(f"    {actual_line_num+1:2d}: {line[:60]}{'...' if len(line) > 60 else ''}")
        
        # Test reassembly
        print("\n🔗 Testing chunk reassembly...")
        reassembled = reassemble_chunks_intelligently([chunk['code'] for chunk in chunks_with_imports], chunks_with_imports)
        
        # Validate reassembled code
        if validate_reassembled_code(reassembled):
            print("✅ Reassembled code validation passed")
        else:
            print("❌ Reassembled code validation failed")
            # Debug: Show the problematic lines
            print("\n🔍 Debug: Lines around indentation error:")
            reassembled_lines = reassembled.split('\n')
            for i, line in enumerate(reassembled_lines):
                if 215 <= i+1 <= 225:  # Show lines around the error
                    indent_level = len(line) - len(line.lstrip())
                    print(f"  {i+1:2d}: {indent_level:2d} | {line}")
        
        # Check for common issues
        print("\n🔍 Checking for common chunking issues...")
        
        # Check for broken functions
        def_count_original = large_code.count('def ')
        def_count_reassembled = reassembled.count('def ')
        if def_count_original == def_count_reassembled:
            print("✅ Function definitions preserved correctly")
        else:
            print(f"❌ Function count mismatch: {def_count_original} vs {def_count_reassembled}")
        
        # Check for broken classes
        class_count_original = large_code.count('class ')
        class_count_reassembled = reassembled.count('class ')
        if class_count_original == class_count_reassembled:
            print("✅ Class definitions preserved correctly")
        else:
            print(f"❌ Class count mismatch: {class_count_original} vs {class_count_reassembled}")
        
        # Check for broken imports
        import_count_original = large_code.count('import ') + large_code.count('from ')
        import_count_reassembled = reassembled.count('import ') + reassembled.count('from ')
        if import_count_original == import_count_reassembled:
            print("✅ Import statements preserved correctly")
        else:
            print(f"❌ Import count mismatch: {import_count_original} vs {import_count_reassembled}")
        
        # Check for balanced structures
        if (reassembled.count('(') == reassembled.count(')') and 
            reassembled.count('[') == reassembled.count(']') and 
            reassembled.count('{') == reassembled.count('}')):
            print("✅ Balanced parentheses, brackets, and braces")
        else:
            print("❌ Unbalanced parentheses, brackets, or braces")
        
        # Test that the reassembled code can be parsed
        print("\n🔍 Testing code parseability...")
        try:
            compile(reassembled, '<reassembled>', 'exec')
            print("✅ Reassembled code compiles successfully")
        except SyntaxError as e:
            print(f"❌ Syntax error in reassembled code: {e}")
        except Exception as e:
            print(f"❌ Error compiling reassembled code: {e}")
        
        print("\n🎯 Comprehensive chunking test completed!")
        
        # Summary
        print("\n📊 Chunking Summary:")
        print(f"  • Original file: {len(large_code)/1024:.1f}KB")
        print(f"  • Split into: {len(chunks)} chunks")
        print(f"  • Average chunk size: {len(large_code)/len(chunks)/1024:.1f}KB")
        print(f"  • All chunks marked as complete structures: {all(chunk.get('complete_structures', False) for chunk in chunks)}")
        print(f"  • Code validation: {'✅ Passed' if validate_reassembled_code(reassembled) else '❌ Failed'}")
        print(f"  • Code compilation: {'✅ Success' if '✅ Reassembled code compiles successfully' in locals() else '❌ Failed'}")
        
    except ImportError as e:
        print(f"❌ Failed to import chunking functions: {e}")
        print("Make sure you're running this from the same directory as genai_uplifter_simplified.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_large_file_chunking() 