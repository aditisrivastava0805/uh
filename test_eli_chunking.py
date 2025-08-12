#!/usr/bin/env python3
"""
Test script to validate chunking with the ELI API
This will test the actual modernization process using chunking
"""

import os
import sys
import json
from genai_uplifter_simplified import (
    get_llm_suggestion,
    analyze_code_for_modernization,
    estimate_tokens_accurately,
    split_code_into_api_chunks,
    ensure_imports_in_first_chunk,
    validate_reassembled_code,
    reassemble_chunks_intelligently
)

def create_medium_test_file():
    """Create a medium-sized Python file that requires chunking"""
    test_code = '''#!/usr/bin/env python3
"""
Medium-sized test file for chunking validation
This file contains Python 2 style code that needs modernization
"""

import os
import sys
import json
import time
from datetime import datetime

class DataProcessor:
    def __init__(self, config_file):
        self.config_file = config_file
        self.data = {}
        self.results = []
        
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config
        except Exception, e:  # Python 2 style exception handling
            print "Error loading config:", str(e)
            return None
    
    def process_data(self, input_data):
        """Process input data using Python 2 patterns"""
        results = []
        
        # Python 2 style iteration
        for key, value in input_data.iteritems():
            if type(value) == dict:
                # Python 2 style string formatting
                print "Processing key: %s" % key
                
                # Python 2 style has_key usage
                if value.has_key('priority'):
                    priority = value['priority']
                else:
                    priority = 0
                
                # Python 2 style print statements
                print "Priority for", key, "is", priority
                
                processed_item = {
                    'key': key,
                    'priority': priority,
                    'timestamp': time.time(),
                    'processed': True
                }
                results.append(processed_item)
        
        return results
    
    def filter_results(self, results, min_priority=1):
        """Filter results based on priority"""
        filtered = []
        for item in results:
            # Python 2 style comparison
            if item['priority'] >= min_priority:
                filtered.append(item)
        
        print "Filtered %d items from %d total" % (len(filtered), len(results))
        return filtered
    
    def save_results(self, results, output_file):
        """Save results to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print "Results saved to:", output_file
            return True
        except Exception, e:  # Python 2 style exception handling
            print "Error saving results:", str(e)
            return False

def create_sample_data():
    """Create sample data for testing"""
    sample_data = {}
    
    for i in xrange(50):  # Python 2 style range
        key = "item_%d" % i
        sample_data[key] = {
            'value': i * 10,
            'priority': i % 5 + 1,
            'category': 'test',
            'active': True if i % 2 == 0 else False
        }
    
    return sample_data

def main():
    """Main function"""
    print "Starting data processing..."
    
    # Create processor instance
    processor = DataProcessor('config.json')
    
    # Load configuration
    config = processor.load_config()
    if config is None:
        print "Failed to load configuration"
        return
    
    # Create sample data
    sample_data = create_sample_data()
    print "Created %d sample items" % len(sample_data)
    
    # Process data
    results = processor.process_data(sample_data)
    print "Processing complete. Got %d results" % len(results)
    
    # Filter results
    filtered_results = processor.filter_results(results, min_priority=2)
    
    # Save results
    output_file = config.get('output_file', 'results.json')
    success = processor.save_results(filtered_results, output_file)
    
    if success:
        print "Data processing completed successfully"
    else:
        print "Data processing failed"

if __name__ == "__main__":
    main()
'''
    
    with open('test_medium_file.py', 'w') as f:
        f.write(test_code)
    
    return 'test_medium_file.py'

def test_eli_chunking():
    """Test chunking with actual ELI API calls"""
    print("Testing ELI API Chunking")
    print("=" * 50)
    
    # Create test file
    test_file = create_medium_test_file()
    print(f"Created test file: {test_file}")
    
    # Read the test file
    with open(test_file, 'r') as f:
        test_code = f.read()
    
    print(f"Test file size: {len(test_code)} characters")
    
    # Estimate tokens
    estimated_tokens = estimate_tokens_accurately(test_code)
    print(f"Estimated tokens: {estimated_tokens:.0f}")
    
    # Check if chunking is needed
    will_need_chunking = estimated_tokens > 5200
    print(f"Will need chunking: {will_need_chunking}")
    
    if will_need_chunking:
        print("\n🔄 Testing chunking approach...")
        
        # Test chunking without API call first
        chunks = split_code_into_api_chunks(test_code)
        print(f"Split into {len(chunks)} chunks:")
        
        for i, chunk in enumerate(chunks):
            chunk_tokens = estimate_tokens_accurately(chunk['code'])
            print(f"  Chunk {i+1}: {len(chunk['code'])} chars, ~{chunk_tokens:.0f} tokens, Complete: {chunk['is_complete']}")
        
        # Ensure imports are in first chunk
        chunks_with_imports = ensure_imports_in_first_chunk(chunks)
        
        # Test reassembly without API call
        reassembled = reassemble_chunks_intelligently(chunks_with_imports)
        
        # Validate reassembled code
        is_valid, validation_errors = validate_reassembled_code(reassembled)
        print(f"\nReassembly validation: {'✅ Passed' if is_valid else '❌ Failed'}")
        if not is_valid:
            print("Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
        
        if is_valid:
            print("\n🚀 Calling ELI API with chunking...")
            
            # Analyze code for modernization
            analysis_findings = analyze_code_for_modernization(test_code)
            print(f"Analysis found {len(analysis_findings)} modernization opportunities")
            
            # Call LLM with chunking
            try:
                modernized_code = get_llm_suggestion(test_code, analysis_findings, "python3.9")
                
                if modernized_code and modernized_code != test_code:
                    print("✅ ELI API chunking successful!")
                    
                    # Save modernized code
                    output_file = 'test_medium_file_modernized.py'
                    with open(output_file, 'w') as f:
                        f.write(modernized_code)
                    
                    print(f"💾 Modernized code saved to: {output_file}")
                    
                    # Check if modernized code is syntactically valid
                    try:
                        compile(modernized_code, output_file, 'exec')
                        print("✅ Modernized code compiles successfully!")
                    except SyntaxError as e:
                        print(f"❌ Syntax error in modernized code: {e}")
                    
                    # Compare sizes
                    original_size = len(test_code)
                    modernized_size = len(modernized_code)
                    print(f"📊 Size comparison: {original_size} -> {modernized_size} chars")
                    
                else:
                    print("❌ ELI API chunking failed or returned no changes")
                    
            except Exception as e:
                print(f"❌ Error during ELI API call: {e}")
        else:
            print("❌ Cannot proceed with API call due to reassembly issues")
    
    else:
        print("\n🚀 Testing direct API call (no chunking needed)...")
        
        # Analyze code for modernization
        analysis_findings = analyze_code_for_modernization(test_code)
        print(f"Analysis found {len(analysis_findings)} modernization opportunities")
        
        # Call LLM directly
        try:
            modernized_code = get_llm_suggestion(test_code, analysis_findings, "python3.9")
            
            if modernized_code and modernized_code != test_code:
                print("✅ ELI API direct call successful!")
                
                # Save modernized code
                output_file = 'test_medium_file_modernized.py'
                with open(output_file, 'w') as f:
                    f.write(modernized_code)
                
                print(f"💾 Modernized code saved to: {output_file}")
                
                # Check if modernized code is syntactically valid
                try:
                    compile(modernized_code, output_file, 'exec')
                    print("✅ Modernized code compiles successfully!")
                except SyntaxError as e:
                    print(f"❌ Syntax error in modernized code: {e}")
                
            else:
                print("❌ ELI API direct call failed or returned no changes")
                
        except Exception as e:
            print(f"❌ Error during ELI API call: {e}")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_eli_chunking()