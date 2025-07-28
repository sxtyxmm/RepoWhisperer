#!/usr/bin/env python3
"""
Test script for RepoWhisperer components.
Tests the parsing functionality without requiring the full model.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.file_parser import FileParser
from parser.prompt_builder import PromptBuilder
from utils.markdown_writer import MarkdownWriter


def create_test_project():
    """Create a temporary test project for testing."""
    temp_dir = tempfile.mkdtemp(prefix="repowhisperer_test_")
    
    # Create a simple Python project structure
    test_files = {
        "main.py": '''#!/usr/bin/env python3
"""
Main entry point for the test application.
"""

import os
import sys
from utils.helper import process_data


class DataProcessor:
    """Processes data for the application."""
    
    def __init__(self, config_path: str):
        """Initialize the processor with config."""
        self.config_path = config_path
        self.data = []
    
    def load_data(self, filepath: str) -> list:
        """Load data from file."""
        with open(filepath, 'r') as f:
            return f.readlines()
    
    def process(self) -> dict:
        """Process the loaded data."""
        return {"status": "processed", "count": len(self.data)}


def main():
    """Main function."""
    processor = DataProcessor("config.yaml")
    result = processor.process()
    print(f"Processing result: {result}")


if __name__ == "__main__":
    main()
''',
        
        "utils/helper.py": '''"""
Utility functions for data processing.
"""

import json
from typing import Any, Dict, List


def process_data(data: List[str]) -> Dict[str, Any]:
    """Process a list of data strings."""
    return {
        "processed_count": len(data),
        "total_length": sum(len(item) for item in data)
    }


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


class ConfigLoader:
    """Loads configuration from various sources."""
    
    def __init__(self):
        self.config = {}
    
    def load_from_file(self, filepath: str) -> Dict[str, Any]:
        """Load config from file."""
        with open(filepath, 'r') as f:
            return json.load(f)
''',
        
        "config.yaml": '''app:
  name: "Test Application"
  version: "1.0.0"
  debug: true

database:
  host: "localhost"
  port: 5432
  name: "testdb"
''',
        
        "README.md": '''# Test Project

This is a test project for RepoWhisperer.
''',
        
        "requirements.txt": '''requests>=2.25.0
pyyaml>=6.0
'''
    }
    
    # Create the files
    for filepath, content in test_files.items():
        full_path = os.path.join(temp_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
    
    return temp_dir


def test_file_parser():
    """Test the file parser functionality."""
    print("Testing FileParser...")
    
    # Create test project
    test_dir = create_test_project()
    
    try:
        # Initialize parser
        parser = FileParser(
            exclude_dirs=['.git', '__pycache__'],
            exclude_files=['*.pyc'],
            supported_extensions=['.py', '.yaml', '.md', '.txt']
        )
        
        # Walk project
        files = parser.walk_project(test_dir)
        print(f"Found {len(files)} files")
        
        # Parse each file
        structures = []
        for file_path in files:
            structure = parser.parse_file(file_path)
            structures.append(structure)
            print(f"Parsed {os.path.basename(file_path)}: "
                  f"{len(structure.classes)} classes, "
                  f"{len(structure.functions)} functions")
        
        # Test summary
        for structure in structures:
            if structure.filepath.endswith('main.py'):
                summary = parser.get_file_summary(structure)
                print(f"Main.py summary: {summary}")
                
                # Verify we found the DataProcessor class
                assert len(structure.classes) >= 1
                assert any(cls.name == 'DataProcessor' for cls in structure.classes)
                print("✅ DataProcessor class found")
                
                # Verify we found the main function
                assert len(structure.functions) >= 1
                assert any(func.name == 'main' for func in structure.functions)
                print("✅ main function found")
        
        print("✅ FileParser test passed!")
        return structures, test_dir
        
    except Exception as e:
        print(f"❌ FileParser test failed: {e}")
        raise
    finally:
        # Don't clean up yet - we'll use it for other tests
        pass


def test_prompt_builder(structures, project_path):
    """Test the prompt builder functionality."""
    print("\nTesting PromptBuilder...")
    
    try:
        builder = PromptBuilder(max_chunk_size=2000, context_lines=3)
        
        # Test project analysis prompt
        prompt = builder.build_project_analysis_prompt(structures, project_path)
        print(f"Generated project analysis prompt: {len(prompt)} characters")
        
        # Verify prompt contains expected elements
        assert "DataProcessor" in prompt
        assert "main.py" in prompt
        assert "helper.py" in prompt
        print("✅ Prompt contains expected class and file names")
        
        # Test architecture prompt
        arch_prompt = builder.build_architecture_prompt(structures, project_path)
        print(f"Generated architecture prompt: {len(arch_prompt)} characters")
        
        # Test usage examples prompt
        usage_prompt = builder.build_usage_examples_prompt(structures, project_path)
        print(f"Generated usage examples prompt: {len(usage_prompt)} characters")
        
        # Test prompt chunking
        long_prompt = "word " * 1000  # Create a long prompt
        chunks = builder.chunk_prompt(long_prompt)
        print(f"Chunked long prompt into {len(chunks)} pieces")
        
        print("✅ PromptBuilder test passed!")
        return [prompt, arch_prompt, usage_prompt]
        
    except Exception as e:
        print(f"❌ PromptBuilder test failed: {e}")
        raise


def test_markdown_writer(prompts):
    """Test the markdown writer functionality."""
    print("\nTesting MarkdownWriter...")
    
    try:
        writer = MarkdownWriter()
        
        # Test with mock LLM responses
        mock_responses = [
            """# Test Project

## Introduction
This is a test project that demonstrates data processing capabilities.

## Installation
```bash
pip install -r requirements.txt
```

## Architecture
The project follows a simple modular architecture:
- `main.py`: Entry point and main processing logic
- `utils/helper.py`: Utility functions and configuration loading

## Usage
```python
from main import DataProcessor
processor = DataProcessor("config.yaml")
result = processor.process()
```
""",
            """## Additional Features
- Configuration management through YAML files
- JSON data processing utilities
- Extensible class-based architecture
"""
        ]
        
        # Generate README
        readme_content = writer.generate_readme(
            mock_responses, 
            "TestProject",
            ["main.py", "utils/helper.py", "config.yaml"]
        )
        
        print(f"Generated README: {len(readme_content)} characters")
        
        # Verify README structure
        assert readme_content.startswith('#')
        assert 'TestProject' in readme_content or 'Test Project' in readme_content
        assert 'Installation' in readme_content
        assert 'Architecture' in readme_content
        print("✅ README has expected structure")
        
        # Test validation
        issues = writer.validate_markdown(readme_content)
        print(f"Validation issues: {len(issues)}")
        
        # Test writing to file
        temp_readme = tempfile.mktemp(suffix=".md")
        writer.write_to_file(readme_content, temp_readme)
        
        # Verify file was written
        assert os.path.exists(temp_readme)
        with open(temp_readme, 'r') as f:
            file_content = f.read()
        assert file_content == readme_content
        print("✅ README file written successfully")
        
        # Clean up
        os.unlink(temp_readme)
        
        print("✅ MarkdownWriter test passed!")
        return readme_content
        
    except Exception as e:
        print(f"❌ MarkdownWriter test failed: {e}")
        raise


def test_integration():
    """Test the integration between all components."""
    print("\nTesting Integration...")
    
    try:
        # Test the dry-run functionality
        from generate_readme import RepoWhisperer
        
        # Create test project
        test_dir = create_test_project()
        
        try:
            # Create a minimal config for testing
            test_config = {
                'model': {
                    'name': 'test-model',
                    'device': 'cpu',
                    'quantization': 'none'
                },
                'parsing': {
                    'exclude_dirs': ['.git', '__pycache__'],
                    'exclude_files': ['*.pyc'],
                    'supported_extensions': ['.py', '.yaml', '.md', '.txt']
                },
                'prompts': {
                    'max_chunk_size': 2000,
                    'context_lines': 3
                }
            }
            
            # Initialize RepoWhisperer without loading the actual model
            repo_whisperer = RepoWhisperer.__new__(RepoWhisperer)
            repo_whisperer.config = test_config
            repo_whisperer._initialize_components()
            repo_whisperer.markdown_writer = MarkdownWriter()
            
            # Test project analysis
            structures = repo_whisperer.analyze_project(test_dir)
            print(f"Analyzed {len(structures)} files")
            
            # Test prompt generation
            prompts = repo_whisperer.generate_prompts(structures, test_dir)
            print(f"Generated {len(prompts)} prompts")
            
            # Test project summary
            repo_whisperer.print_project_summary(structures)
            
            print("✅ Integration test passed!")
            
        finally:
            # Clean up test directory
            shutil.rmtree(test_dir)
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise


def main():
    """Run all tests."""
    print("🧪 Running RepoWhisperer Component Tests")
    print("=" * 50)
    
    try:
        # Test file parser
        structures, test_dir = test_file_parser()
        
        # Test prompt builder
        prompts = test_prompt_builder(structures, test_dir)
        
        # Test markdown writer
        readme_content = test_markdown_writer(prompts)
        
        # Clean up test directory
        shutil.rmtree(test_dir)
        
        # Test integration
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("RepoWhisperer is ready to use!")
        print("\nTo generate a README for a project:")
        print("python generate_readme.py --repo /path/to/your/project")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
