#!/usr/bin/env python3
"""
Large test file to demonstrate the improved chunking strategy.
This file should be large enough to trigger chunking.
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime, timedelta
import hashlib
import base64

class LargeDataProcessor:
    """Process large amounts of data with various methods."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data = []
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        
    def load_data(self, file_path: str) -> List:
        """Load data from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.data = data
            return data
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return []
    
    def process_data(self) -> List:
        """Process the loaded data."""
        if not self.data:
            return []
        
        self.start_time = time.time()
        processed = []
        
        for item in self.data:
            try:
                if self._validate_item(item):
                    processed_item = self._transform_item(item)
                    processed.append(processed_item)
                    self.processed_count += 1
                else:
                    self.error_count += 1
            except Exception as e:
                logging.error(f"Error processing item: {e}")
                self.error_count += 1
        
        return processed
    
    def _validate_item(self, item: Dict) -> bool:
        """Validate a single item."""
        required_fields = ['id', 'name', 'value', 'timestamp']
        return all(field in item for field in required_fields)
    
    def _transform_item(self, item: Dict) -> Dict:
        """Transform a single item."""
        return {
            'id': str(item['id']),
            'name': item['name'].upper(),
            'value': float(item['value']) * 1.1,
            'timestamp': item['timestamp'],
            'hash': hashlib.md5(str(item).encode()).hexdigest(),
            'processed_at': datetime.now().isoformat()
        }
    
    def get_statistics(self) -> Dict:
        """Get processing statistics."""
        if not self.start_time:
            return {}
        
        duration = time.time() - self.start_time
        return {
            'total_items': len(self.data),
            'processed_items': self.processed_count,
            'error_items': self.error_count,
            'success_rate': self.processed_count / len(self.data) if self.data else 0,
            'processing_time': duration,
            'items_per_second': self.processed_count / duration if duration > 0 else 0
        }

class DataValidator:
    """Validate data integrity and format."""
    
    def __init__(self, rules: Dict):
        self.rules = rules
        self.validation_errors = []
    
    def validate_dataset(self, data: List) -> Tuple[bool, List[str]]:
        """Validate entire dataset."""
        self.validation_errors = []
        
        for i, item in enumerate(data):
            if not self._validate_single_item(item, i):
                self.validation_errors.append(f"Item {i}: Invalid format")
        
        return len(self.validation_errors) == 0, self.validation_errors
    
    def _validate_single_item(self, item: Dict, index: int) -> bool:
        """Validate a single item."""
        # Check required fields
        for field in self.rules.get('required_fields', []):
            if field not in item:
                return False
        
        # Check data types
        for field, expected_type in self.rules.get('field_types', {}).items():
            if field in item:
                if not isinstance(item[field], expected_type):
                    return False
        
        # Check value ranges
        for field, range_info in self.rules.get('value_ranges', {}).items():
            if field in item:
                value = item[field]
                if 'min' in range_info and value < range_info['min']:
                    return False
                if 'max' in range_info and value > range_info['max']:
                    return False
        
        return True

class DataExporter:
    """Export processed data to various formats."""
    
    def __init__(self, output_config: Dict):
        self.output_config = output_config
        self.export_formats = ['json', 'csv', 'xml']
    
    def export_data(self, data: List, format_type: str, output_path: str) -> bool:
        """Export data to specified format."""
        if format_type not in self.export_formats:
            logging.error(f"Unsupported format: {format_type}")
            return False
        
        try:
            if format_type == 'json':
                return self._export_json(data, output_path)
            elif format_type == 'csv':
                return self._export_csv(data, output_path)
            elif format_type == 'xml':
                return self._export_xml(data, output_path)
        except Exception as e:
            logging.error(f"Export error: {e}")
            return False
        
        return False
    
    def _export_json(self, data: List, output_path: str) -> bool:
        """Export data to JSON format."""
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    
    def _export_csv(self, data: List, output_path: str) -> bool:
        """Export data to CSV format."""
        if not data:
            return False
        
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return True
    
    def _export_xml(self, data: List, output_path: str) -> bool:
        """Export data to XML format."""
        if not data:
            return False
        
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<data>\n'
        for item in data:
            xml_content += '  <item>\n'
            for key, value in item.items():
                xml_content += f'    <{key}>{value}</{key}>\n'
            xml_content += '  </item>\n'
        xml_content += '</data>'
        
        with open(output_path, 'w') as f:
            f.write(xml_content)
        return True

def create_sample_data(count: int) -> List[Dict]:
    """Create sample data for testing."""
    data = []
    base_time = datetime.now()
    
    for i in range(count):
        item = {
            'id': i + 1,
            'name': f'Item_{i+1}',
            'value': round(100 + i * 0.5, 2),
            'timestamp': (base_time + timedelta(minutes=i)).isoformat(),
            'category': f'Category_{i % 5}',
            'priority': i % 3 + 1
        }
        data.append(item)
    
    return data

def main():
    """Main function to run the large data processor."""
    # Configuration
    config = {
        'input_file': 'large_data.json',
        'output_file': 'processed_large_data.json',
        'multiplier': 1.1,
        'validation_rules': {
            'required_fields': ['id', 'name', 'value', 'timestamp'],
            'field_types': {
                'id': int,
                'name': str,
                'value': (int, float),
                'timestamp': str
            },
            'value_ranges': {
                'value': {'min': 0, 'max': 10000},
                'priority': {'min': 1, 'max': 5}
            }
        }
    }
    
    # Create sample data if input file doesn't exist
    if not os.path.exists(config['input_file']):
        print("Creating sample data...")
        sample_data = create_sample_data(1000)
        with open(config['input_file'], 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"Created {len(sample_data)} sample items")
    
    # Initialize components
    processor = LargeDataProcessor(config)
    validator = DataValidator(config['validation_rules'])
    exporter = DataExporter({'output_dir': '.'})
    
    # Load and process data
    print("Loading data...")
    data = processor.load_data(config['input_file'])
    
    if data:
        print(f"Loaded {len(data)} items")
        
        # Validate data
        print("Validating data...")
        is_valid, errors = validator.validate_dataset(data)
        if not is_valid:
            print(f"Validation failed with {len(errors)} errors")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  {error}")
            return
        
        # Process data
        print("Processing data...")
        processed = processor.process_data()
        
        # Get statistics
        stats = processor.get_statistics()
        print(f"Processing completed:")
        print(f"  Total items: {stats['total_items']}")
        print(f"  Processed: {stats['processed_items']}")
        print(f"  Errors: {stats['error_items']}")
        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Processing time: {stats['processing_time']:.2f}s")
        print(f"  Items per second: {stats['items_per_second']:.2f}")
        
        # Export data
        print("Exporting data...")
        if exporter.export_data(processed, 'json', config['output_file']):
            print(f"Data exported to {config['output_file']}")
        else:
            print("Export failed")
    else:
        print("No data to process")

if __name__ == "__main__":
    main() 