#!/usr/bin/env python3
"""
RepoWhisperer - Auto-README Generator using DeepSeek-Coder

A Python-based system that uses DeepSeek-Coder 33B to analyze GitHub projects
and automatically generate detailed README.md files.

Usage:
    python generate_readme.py --repo ./my_project
    python generate_readme.py --repo /path/to/project --output custom_readme.md
    python generate_readme.py --repo . --config custom_config.yaml
"""

import argparse
import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.file_parser import FileParser
from parser.prompt_builder import PromptBuilder
from model.inference import LocalInferenceWrapper
from utils.markdown_writer import MarkdownWriter


class RepoWhisperer:
    """Main class for the RepoWhisperer README generator."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize RepoWhisperer with configuration."""
        self.config = self._load_config(config_path)
        self.file_parser = None
        self.prompt_builder = None
        self.markdown_writer = MarkdownWriter()
        
        # Initialize components
        self._initialize_components()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            print(f"Config file {config_path} not found. Using default configuration.")
            return self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'model': {
                'name': 'deepseek-ai/deepseek-coder-33b-instruct',
                'device': 'auto',
                'quantization': '4bit',
                'max_tokens': 4096,
                'temperature': 0.1,
                'top_p': 0.95
            },
            'parsing': {
                'exclude_dirs': ['.git', '__pycache__', 'node_modules', 'venv'],
                'exclude_files': ['*.pyc', '*.log'],
                'supported_extensions': ['.py', '.js', '.ts', '.md', '.yaml', '.json']
            },
            'prompts': {
                'max_chunk_size': 3000,
                'context_lines': 5
            }
        }
    
    def _initialize_components(self):
        """Initialize parser and prompt builder with config."""
        parsing_config = self.config.get('parsing', {})
        prompt_config = self.config.get('prompts', {})
        
        self.file_parser = FileParser(
            exclude_dirs=parsing_config.get('exclude_dirs', []),
            exclude_files=parsing_config.get('exclude_files', []),
            supported_extensions=parsing_config.get('supported_extensions', [])
        )
        
        self.prompt_builder = PromptBuilder(
            max_chunk_size=prompt_config.get('max_chunk_size', 3000),
            context_lines=prompt_config.get('context_lines', 5)
        )
    
    def analyze_project(self, project_path: str) -> List[Any]:
        """Analyze the project structure and extract information."""
        print(f"Analyzing project: {project_path}")
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        # Walk through project and collect files
        print("Collecting project files...")
        file_paths = self.file_parser.walk_project(project_path)
        print(f"Found {len(file_paths)} files to analyze")
        
        if not file_paths:
            print("No supported files found in the project!")
            return []
        
        # Parse each file
        print("Parsing files...")
        structures = []
        
        for i, file_path in enumerate(file_paths[:50]):  # Limit to first 50 files
            try:
                print(f"Parsing {i+1}/{min(len(file_paths), 50)}: {os.path.basename(file_path)}")
                structure = self.file_parser.parse_file(file_path)
                structures.append(structure)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                continue
        
        print(f"Successfully parsed {len(structures)} files")
        return structures
    
    def generate_prompts(self, structures: List[Any], project_path: str) -> List[str]:
        """Generate prompts for the LLM."""
        print("Building prompts for LLM...")
        
        # Build comprehensive project analysis prompt
        main_prompt = self.prompt_builder.build_project_analysis_prompt(structures, project_path)
        
        # Split into chunks if necessary
        prompt_chunks = self.prompt_builder.chunk_prompt(main_prompt)
        
        print(f"Generated {len(prompt_chunks)} prompt chunks")
        
        # If we have many files, also generate specific prompts
        if len(structures) > 10:
            # Architecture analysis
            arch_prompt = self.prompt_builder.build_architecture_prompt(structures, project_path)
            arch_chunks = self.prompt_builder.chunk_prompt(arch_prompt)
            
            # Usage examples
            usage_prompt = self.prompt_builder.build_usage_examples_prompt(structures, project_path)
            usage_chunks = self.prompt_builder.chunk_prompt(usage_prompt)
            
            # Combine all chunks
            all_chunks = prompt_chunks + arch_chunks + usage_chunks
            print(f"Total prompt chunks including specialized prompts: {len(all_chunks)}")
            return all_chunks
        
        return prompt_chunks
    
    def generate_with_llm(self, prompts: List[str]) -> List[str]:
        """Generate responses using the LLM."""
        print("Initializing model for inference...")
        
        try:
            with LocalInferenceWrapper(self.config) as model:
                print("Model loaded successfully!")
                print(f"Model info: {model.get_model_info()}")
                
                # Generate responses
                print(f"Generating responses for {len(prompts)} prompts...")
                responses = model.generate_in_chunks(prompts)
                
                print("Generation completed!")
                return responses
                
        except Exception as e:
            print(f"Error during model inference: {e}")
            print("Traceback:")
            traceback.print_exc()
            
            # Fallback: generate a basic README template
            print("Falling back to template-based README generation...")
            return self._generate_fallback_readme()
    
    def _generate_fallback_readme(self) -> List[str]:
        """Generate a basic README template when model fails."""
        template = """# Project README

This README was generated when the AI model was unavailable.

## About
This project contains source code that needs documentation.

## Installation
```bash
# Add installation instructions here
pip install -r requirements.txt
```

## Usage
```bash
# Add usage examples here
python main.py
```

## Structure
The project contains multiple source files organized in a structured manner.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
Please check the project for license information.
"""
        return [template]
    
    def generate_readme(self, project_path: str, output_path: str = None) -> str:
        """Generate README for the specified project."""
        try:
            # Analyze project
            structures = self.analyze_project(project_path)
            
            if not structures:
                raise ValueError("No files could be parsed from the project")
            
            # Generate prompts
            prompts = self.generate_prompts(structures, project_path)
            
            # Generate with LLM
            responses = self.generate_with_llm(prompts)
            
            # Create README
            project_name = os.path.basename(os.path.abspath(project_path))
            readme_content = self.markdown_writer.generate_readme(
                responses, project_name, [s.filepath for s in structures]
            )
            
            # Validate the generated README
            issues = self.markdown_writer.validate_markdown(readme_content)
            if issues:
                print("README validation issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            
            # Write to file
            if output_path is None:
                output_path = os.path.join(project_path, "README.md")
            
            self.markdown_writer.write_to_file(readme_content, output_path)
            
            return readme_content
            
        except Exception as e:
            print(f"Error generating README: {e}")
            traceback.print_exc()
            raise
    
    def print_project_summary(self, structures: List[Any]):
        """Print a summary of the analyzed project."""
        if not structures:
            print("No files analyzed.")
            return
        
        print("\n" + "="*50)
        print("PROJECT ANALYSIS SUMMARY")
        print("="*50)
        
        total_files = len(structures)
        total_classes = sum(len(s.classes) for s in structures)
        total_functions = sum(len(s.functions) for s in structures)
        total_lines = sum(len(s.raw_content.split('\n')) for s in structures)
        
        print(f"Total Files: {total_files}")
        print(f"Total Classes: {total_classes}")
        print(f"Total Functions: {total_functions}")
        print(f"Total Lines of Code: {total_lines}")
        
        # Language breakdown
        languages = {}
        for structure in structures:
            lang = structure.language
            languages[lang] = languages.get(lang, 0) + 1
        
        print("\nLanguage Breakdown:")
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang}: {count} files")
        
        # Top files by size
        print("\nLargest Files:")
        sorted_files = sorted(structures, key=lambda s: len(s.raw_content), reverse=True)
        for structure in sorted_files[:5]:
            size = len(structure.raw_content)
            filename = os.path.basename(structure.filepath)
            print(f"  {filename}: {size:,} characters")
        
        print("="*50 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RepoWhisperer - Auto-README Generator using DeepSeek-Coder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_readme.py --repo ./my_project
  python generate_readme.py --repo /path/to/project --output custom_readme.md
  python generate_readme.py --repo . --config custom_config.yaml --verbose
        """
    )
    
    parser.add_argument(
        '--repo', '-r',
        required=True,
        help='Path to the repository/project to analyze'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output path for the README.md file (default: <repo>/README.md)'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze project but don\'t generate README (useful for testing)'
    )
    
    args = parser.parse_args()
    
    # Initialize RepoWhisperer
    try:
        repo_whisperer = RepoWhisperer(args.config)
        
        if args.dry_run:
            # Just analyze and print summary
            print("Running in dry-run mode - analyzing project only...")
            structures = repo_whisperer.analyze_project(args.repo)
            repo_whisperer.print_project_summary(structures)
            print("Dry run completed. No README generated.")
            return
        
        # Generate README
        print("Starting README generation...")
        readme_content = repo_whisperer.generate_readme(args.repo, args.output)
        
        if args.verbose:
            print("\nGenerated README preview:")
            print("-" * 50)
            print(readme_content[:500] + "..." if len(readme_content) > 500 else readme_content)
            print("-" * 50)
        
        print("\n✅ README generation completed successfully!")
        
        output_file = args.output or os.path.join(args.repo, "README.md")
        print(f"📄 README written to: {output_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
