#!/usr/bin/env python3
"""
Test script to demonstrate the improved chunking strategy.
"""

def test_chunking_strategy():
    """Test the improved chunking with a sample Python file."""
    
    # Sample Python code that would normally cause chunking issues
    sample_code = '''#!/usr/bin/env python3
"""
Sample Python file with multiple functions and classes.
"""

import os
import sys
import json
from typing import List, Dict, Optional

class DataProcessor:
    """Process data with various methods."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data = []
    
    def load_data(self, file_path: str) -> List:
        """Load data from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.data = data
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def process_data(self) -> List:
        """Process the loaded data."""
        if not self.data:
            return []
        
        processed = []
        for item in self.data:
            if self._validate_item(item):
                processed.append(self._transform_item(item))
        
        return processed
    
    def _validate_item(self, item: Dict) -> bool:
        """Validate a single item."""
        required_fields = ['id', 'name', 'value']
        return all(field in item for field in required_fields)
    
    def _transform_item(self, item: Dict) -> Dict:
        """Transform a single item."""
        return {
            'id': str(item['id']),
            'name': item['name'].upper(),
            'value': float(item['value']) * 1.1
        }

def main():
    """Main function to run the data processor."""
    config = {
        'input_file': 'data.json',
        'output_file': 'processed_data.json',
        'multiplier': 1.1
    }
    
    processor = DataProcessor(config)
    
    # Load and process data
    data = processor.load_data(config['input_file'])
    if data:
        processed = processor.process_data()
        
        # Save processed data
        with open(config['output_file'], 'w') as f:
            json.dump(processed, f, indent=2)
        
        print(f"Processed {len(processed)} items successfully")
    else:
        print("No data to process")

if __name__ == "__main__":
    main()
'''

    print("🧪 Testing Improved Chunking Strategy")
    print("=" * 50)
    
    # Import the chunking functions
    try:
        from genai_uplifter_simplified import (
            split_code_into_api_chunks, 
            ensure_imports_in_first_chunk,
            validate_reassembled_code
        )
        
        print("✅ Successfully imported chunking functions")
        
        # Test chunking
        print("\n📦 Testing code chunking...")
        chunks = split_code_into_api_chunks(sample_code)
        
        print(f"📊 Split into {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            size_kb = len(chunk['code']) / 1024
            complete = chunk.get('complete_structures', False)
            print(f"  Chunk {i+1}: {size_kb:.1f}KB, Complete: {complete}")
        
        # Test import preservation
        print("\n🔧 Testing import preservation...")
        chunks_with_imports = ensure_imports_in_first_chunk(chunks)
        
        # Check if imports are in first chunk
        first_chunk = chunks_with_imports[0]['code']
        import_lines = [line for line in first_chunk.split('\n') if line.strip().startswith(('import ', 'from '))]
        print(f"📦 Imports in first chunk: {len(import_lines)}")
        for imp in import_lines:
            print(f"  {imp.strip()}")
        
        # Debug: Show the first few lines of the first chunk
        print("\n🔍 First chunk content (first 20 lines):")
        first_chunk_lines = first_chunk.split('\n')
        for i, line in enumerate(first_chunk_lines[:20]):
            print(f"  {i+1:2d}: {line}")
        
        # Test reassembly
        print("\n🔗 Testing chunk reassembly...")
        reassembled = '\n'.join([chunk['code'] for chunk in chunks_with_imports])
        
        # Validate reassembled code
        if validate_reassembled_code(reassembled):
            print("✅ Reassembled code validation passed")
        else:
            print("❌ Reassembled code validation failed")
            # Debug: Show the problematic lines
            print("\n🔍 Debug: Lines around indentation error:")
            reassembled_lines = reassembled.split('\n')
            for i, line in enumerate(reassembled_lines):
                if 45 <= i+1 <= 55:  # Show lines around the error
                    indent_level = len(line) - len(line.lstrip())
                    print(f"  {i+1:2d}: {indent_level:2d} | {line}")
        
        # Check for common issues
        print("\n🔍 Checking for common chunking issues...")
        
        # Check for broken functions
        if 'def ' in reassembled and 'def ' in sample_code:
            def_count_original = sample_code.count('def ')
            def_count_reassembled = reassembled.count('def ')
            if def_count_original == def_count_reassembled:
                print("✅ Function definitions preserved correctly")
            else:
                print(f"❌ Function count mismatch: {def_count_original} vs {def_count_reassembled}")
        
        # Check for broken classes
        if 'class ' in reassembled and 'class ' in sample_code:
            class_count_original = sample_code.count('class ')
            class_count_reassembled = reassembled.count('class ')
            if class_count_original == class_count_reassembled:
                print("✅ Class definitions preserved correctly")
            else:
                print(f"❌ Class count mismatch: {class_count_original} vs {class_count_reassembled}")
        
        # Check for broken imports
        if 'import ' in reassembled and 'import ' in sample_code:
            import_count_original = sample_code.count('import ') + sample_code.count('from ')
            import_count_reassembled = reassembled.count('import ') + reassembled.count('from ')
            if import_count_original == import_count_reassembled:
                print("✅ Import statements preserved correctly")
            else:
                print(f"❌ Import count mismatch: {import_count_original} vs {import_count_reassembled}")
        
        print("\n🎯 Chunking test completed!")
        
    except ImportError as e:
        print(f"❌ Failed to import chunking functions: {e}")
        print("Make sure you're running this from the same directory as genai_uplifter_simplified.py")

if __name__ == "__main__":
    test_chunking_strategy() 