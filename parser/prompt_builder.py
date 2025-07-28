from typing import List, Dict, Any
from .file_parser import CodeStructure, ClassInfo, FunctionInfo
import os


class PromptBuilder:
    """Builds prompts for the LLM to analyze code and generate README content."""
    
    def __init__(self, max_chunk_size: int = 3000, context_lines: int = 5):
        self.max_chunk_size = max_chunk_size
        self.context_lines = context_lines
    
    def build_project_analysis_prompt(self, structures: List[CodeStructure], 
                                    project_path: str) -> str:
        """Build a comprehensive prompt for project analysis."""
        
        project_name = os.path.basename(project_path)
        
        prompt = f"""You are a senior software engineer analyzing a codebase called "{project_name}". 
Your task is to understand the project architecture and generate content for a comprehensive README.md file.

## Project Overview
Project Name: {project_name}
Project Path: {project_path}
Total Files: {len(structures)}

## File Structure Analysis
"""
        
        # Add file structure overview
        for structure in structures:
            rel_path = os.path.relpath(structure.filepath, project_path)
            prompt += f"\n### File: {rel_path}\n"
            prompt += f"- Language: {structure.language}\n"
            prompt += f"- Classes: {len(structure.classes)}\n"
            prompt += f"- Functions: {len(structure.functions)}\n"
            prompt += f"- Imports: {len(structure.imports)}\n"
            
            if structure.docstring:
                prompt += f"- Module Description: {structure.docstring[:200]}...\n"
        
        prompt += "\n\n## Detailed Code Analysis\n"
        
        # Add detailed analysis for key files
        for structure in structures[:10]:  # Limit to first 10 files to avoid token overflow
            prompt += self._build_file_analysis_section(structure, project_path)
        
        prompt += """

## Task
Based on this code analysis, generate a comprehensive README.md with the following sections:

1. **Project Title and Description**: A clear, engaging description of what this project does
2. **Installation Instructions**: How to set up and install the project
3. **Architecture Overview**: High-level explanation of the project structure and design patterns
4. **File Structure**: Breakdown of key files and their purposes
5. **Key Components**: Description of main classes, functions, and modules
6. **Usage Examples**: How to use the project with code examples if applicable
7. **Contributing Guidelines**: How others can contribute to the project
8. **License**: License information if available

Please write the README in professional, clear markdown format that would be suitable for a GitHub repository.
Focus on making it useful for both new users and potential contributors.
"""
        
        return prompt
    
    def _build_file_analysis_section(self, structure: CodeStructure, project_path: str) -> str:
        """Build detailed analysis section for a single file."""
        rel_path = os.path.relpath(structure.filepath, project_path)
        section = f"\n### Detailed Analysis: {rel_path}\n"
        
        if structure.docstring:
            section += f"**Purpose**: {structure.docstring}\n\n"
        
        # Add imports
        if structure.imports:
            section += "**Key Dependencies**:\n"
            for imp in structure.imports[:5]:  # Limit to first 5
                section += f"- {imp}\n"
            if len(structure.imports) > 5:
                section += f"- ... and {len(structure.imports) - 5} more\n"
            section += "\n"
        
        # Add classes
        if structure.classes:
            section += "**Classes**:\n"
            for cls in structure.classes:
                section += f"- `{cls.name}` (line {cls.line_number})"
                if cls.docstring:
                    section += f": {cls.docstring[:100]}..."
                section += "\n"
                
                if cls.methods:
                    section += f"  - Methods: {', '.join([m.name for m in cls.methods[:3]])}"
                    if len(cls.methods) > 3:
                        section += f" + {len(cls.methods) - 3} more"
                    section += "\n"
            section += "\n"
        
        # Add functions
        if structure.functions:
            section += "**Functions**:\n"
            for func in structure.functions:
                section += f"- `{func.name}()` (line {func.line_number})"
                if func.docstring:
                    section += f": {func.docstring[:100]}..."
                section += "\n"
            section += "\n"
        
        # Add code snippet for context
        lines = structure.raw_content.split('\n')
        if len(lines) <= 20:  # For small files, include full content
            section += "**Code Content**:\n```" + structure.language + "\n"
            section += structure.raw_content[:1000]  # Limit content size
            if len(structure.raw_content) > 1000:
                section += "\n... (truncated)"
            section += "\n```\n"
        else:  # For larger files, include key sections
            section += "**Key Code Sections**:\n"
            if structure.classes:
                # Show first class definition
                first_class = structure.classes[0]
                start_line = max(0, first_class.line_number - 1 - self.context_lines)
                end_line = min(len(lines), first_class.line_number + 10)
                section += f"```{structure.language}\n"
                section += '\n'.join(lines[start_line:end_line])
                section += "\n```\n"
            elif structure.functions:
                # Show first function definition
                first_func = structure.functions[0]
                start_line = max(0, first_func.line_number - 1 - self.context_lines)
                end_line = min(len(lines), first_func.line_number + 10)
                section += f"```{structure.language}\n"
                section += '\n'.join(lines[start_line:end_line])
                section += "\n```\n"
        
        return section
    
    def build_architecture_prompt(self, structures: List[CodeStructure], 
                                project_path: str) -> str:
        """Build a prompt specifically for architecture analysis."""
        
        prompt = f"""Analyze the architecture of this codebase and provide a structured overview.

## Project Structure
"""
        
        # Group files by directory
        dir_structure = {}
        for structure in structures:
            rel_path = os.path.relpath(structure.filepath, project_path)
            dir_name = os.path.dirname(rel_path) or "root"
            if dir_name not in dir_structure:
                dir_structure[dir_name] = []
            dir_structure[dir_name].append(structure)
        
        for dir_name, files in dir_structure.items():
            prompt += f"\n### Directory: {dir_name}\n"
            for structure in files:
                filename = os.path.basename(structure.filepath)
                prompt += f"- {filename} ({structure.language}): "
                prompt += f"{len(structure.classes)} classes, {len(structure.functions)} functions\n"
        
        # Analyze dependencies and patterns
        prompt += "\n## Dependency Analysis\n"
        all_imports = set()
        for structure in structures:
            all_imports.update(structure.imports)
        
        external_deps = [imp for imp in all_imports if not imp.startswith('.')]
        internal_deps = [imp for imp in all_imports if imp.startswith('.')]
        
        prompt += f"External Dependencies: {len(external_deps)}\n"
        prompt += f"Internal Imports: {len(internal_deps)}\n"
        
        if external_deps:
            prompt += "\nKey External Libraries:\n"
            for dep in sorted(external_deps)[:10]:
                prompt += f"- {dep}\n"
        
        prompt += """

## Architecture Analysis Task
Based on this structure, provide:

1. **Architecture Pattern**: What design pattern(s) does this project follow? (MVC, layered, microservices, etc.)
2. **Entry Points**: What are the main entry points to the application?
3. **Core Components**: What are the main functional areas/modules?
4. **Data Flow**: How does data flow through the application?
5. **Configuration**: How is the application configured?
6. **Testing Strategy**: What testing approach is used?

Format your response as a clear, structured analysis suitable for a README's Architecture section.
"""
        
        return prompt
    
    def build_usage_examples_prompt(self, structures: List[CodeStructure], 
                                  project_path: str) -> str:
        """Build a prompt for generating usage examples."""
        
        # Look for main files, CLI scripts, or API endpoints
        main_files = []
        cli_files = []
        test_files = []
        
        for structure in structures:
            filename = os.path.basename(structure.filepath).lower()
            if 'main' in filename or filename == '__main__.py':
                main_files.append(structure)
            elif 'cli' in filename or 'command' in filename:
                cli_files.append(structure)
            elif 'test' in filename:
                test_files.append(structure)
        
        prompt = f"""Generate usage examples for this project based on the code analysis.

## Entry Points Analysis
"""
        
        if main_files:
            prompt += "### Main Files:\n"
            for structure in main_files:
                prompt += f"- {os.path.basename(structure.filepath)}\n"
                if structure.functions:
                    prompt += f"  Functions: {', '.join([f.name for f in structure.functions[:3]])}\n"
        
        if cli_files:
            prompt += "### CLI Files:\n"
            for structure in cli_files:
                prompt += f"- {os.path.basename(structure.filepath)}\n"
        
        # Look for configuration files
        config_files = [s for s in structures if any(
            ext in s.filepath.lower() for ext in ['.yaml', '.yml', '.json', '.toml', '.ini', 'config']
        )]
        
        if config_files:
            prompt += "### Configuration Files:\n"
            for structure in config_files:
                prompt += f"- {os.path.basename(structure.filepath)}\n"
        
        prompt += """

## Task
Generate practical usage examples including:

1. **Installation**: Step-by-step installation instructions
2. **Basic Usage**: Simple examples of how to use the project
3. **Configuration**: How to configure the project for different use cases
4. **CLI Usage**: Command-line examples if applicable
5. **API Usage**: Code examples if it's a library or has an API
6. **Advanced Usage**: More complex usage scenarios

Make the examples practical and copy-pasteable. Include code blocks with proper syntax highlighting.
"""
        
        return prompt
    
    def chunk_prompt(self, prompt: str) -> List[str]:
        """Split a large prompt into smaller chunks."""
        if len(prompt) <= self.max_chunk_size:
            return [prompt]
        
        chunks = []
        words = prompt.split()
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= self.max_chunk_size:
                current_chunk += " " + word if current_chunk else word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
