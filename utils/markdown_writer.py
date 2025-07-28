from typing import List, Dict, Any, Optional
from datetime import datetime
import re


class MarkdownWriter:
    """Handles formatting and writing of README.md files."""
    
    def __init__(self):
        self.sections = {}
        self.project_name = ""
        self.project_description = ""
    
    def set_project_info(self, name: str, description: str = ""):
        """Set basic project information."""
        self.project_name = name
        self.project_description = description
    
    def add_section(self, section_name: str, content: str, level: int = 2):
        """Add a section to the README."""
        self.sections[section_name] = {
            'content': content.strip(),
            'level': level
        }
    
    def generate_title_section(self, project_name: str, description: str = "") -> str:
        """Generate the title section."""
        title_section = f"# {project_name}\n\n"
        
        if description:
            title_section += f"{description}\n\n"
        
        # Add badges (placeholder - can be customized)
        title_section += self._generate_badges()
        
        return title_section
    
    def _generate_badges(self) -> str:
        """Generate common badges for the README."""
        badges = [
            "![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)",
            "![License](https://img.shields.io/badge/license-MIT-green.svg)",
            "![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)"
        ]
        
        return " ".join(badges) + "\n\n"
    
    def generate_table_of_contents(self) -> str:
        """Generate table of contents based on sections."""
        toc = "## Table of Contents\n\n"
        
        section_order = [
            'installation', 'quick_start', 'architecture', 'features',
            'file_structure', 'key_components', 'usage', 'examples',
            'configuration', 'api', 'contributing', 'testing', 'license'
        ]
        
        for section_key in section_order:
            if section_key in self.sections:
                section_title = self._format_section_title(section_key)
                anchor = self._create_anchor(section_title)
                toc += f"- [{section_title}](#{anchor})\n"
        
        # Add any remaining sections not in the standard order
        for section_key in self.sections:
            if section_key not in section_order:
                section_title = self._format_section_title(section_key)
                anchor = self._create_anchor(section_title)
                toc += f"- [{section_title}](#{anchor})\n"
        
        return toc + "\n"
    
    def _format_section_title(self, section_key: str) -> str:
        """Format section key into a proper title."""
        title_map = {
            'installation': 'Installation',
            'quick_start': 'Quick Start',
            'architecture': 'Architecture',
            'features': 'Features',
            'file_structure': 'File Structure',
            'key_components': 'Key Components',
            'usage': 'Usage',
            'examples': 'Examples',
            'configuration': 'Configuration',
            'api': 'API Reference',
            'contributing': 'Contributing',
            'testing': 'Testing',
            'license': 'License'
        }
        
        return title_map.get(section_key, section_key.replace('_', ' ').title())
    
    def _create_anchor(self, title: str) -> str:
        """Create GitHub-style anchor link."""
        anchor = title.lower()
        anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        return anchor
    
    def format_code_block(self, code: str, language: str = "") -> str:
        """Format code in a markdown code block."""
        return f"```{language}\n{code}\n```"
    
    def format_file_tree(self, file_paths: List[str], project_root: str = "") -> str:
        """Format file paths as a tree structure."""
        tree = "```\n"
        
        # Group files by directory
        dirs = {}
        for path in sorted(file_paths):
            if project_root:
                # Make path relative to project root
                import os
                path = os.path.relpath(path, project_root)
            
            parts = path.split('/')
            current = dirs
            
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {} if i < len(parts) - 1 else None
                current = current[part] if current[part] is not None else {}
        
        def print_tree(node, prefix="", is_last=True):
            if isinstance(node, dict):
                items = list(node.items())
                for i, (name, child) in enumerate(items):
                    is_last_item = i == len(items) - 1
                    tree_part = "└── " if is_last_item else "├── "
                    tree_lines.append(f"{prefix}{tree_part}{name}")
                    
                    if child is not None:
                        extension = "    " if is_last_item else "│   "
                        print_tree(child, prefix + extension, is_last_item)
        
        tree_lines = []
        print_tree(dirs)
        tree += "\n".join(tree_lines)
        tree += "\n```"
        
        return tree
    
    def format_class_documentation(self, classes: List[Dict[str, Any]]) -> str:
        """Format class documentation."""
        if not classes:
            return ""
        
        doc = "### Classes\n\n"
        
        for cls in classes:
            doc += f"#### `{cls['name']}`\n\n"
            
            if cls.get('docstring'):
                doc += f"{cls['docstring']}\n\n"
            
            if cls.get('methods'):
                doc += "**Methods:**\n"
                for method in cls['methods'][:5]:  # Limit to first 5 methods
                    doc += f"- `{method['name']}()`"
                    if method.get('docstring'):
                        doc += f": {method['docstring'][:100]}..."
                    doc += "\n"
                
                if len(cls['methods']) > 5:
                    doc += f"- ... and {len(cls['methods']) - 5} more methods\n"
                doc += "\n"
        
        return doc
    
    def format_function_documentation(self, functions: List[Dict[str, Any]]) -> str:
        """Format function documentation."""
        if not functions:
            return ""
        
        doc = "### Functions\n\n"
        
        for func in functions:
            doc += f"#### `{func['name']}()`\n\n"
            
            if func.get('docstring'):
                doc += f"{func['docstring']}\n\n"
            
            if func.get('parameters'):
                doc += "**Parameters:**\n"
                for param in func['parameters']:
                    doc += f"- `{param}`\n"
                doc += "\n"
        
        return doc
    
    def clean_llm_response(self, response: str) -> str:
        """Clean up LLM response and extract markdown content."""
        # Remove any instruction artifacts
        cleaned = response.strip()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = [
            "Here's the README.md content:",
            "Here is the README.md:",
            "# README.md",
            "```markdown",
            "```md"
        ]
        
        suffixes_to_remove = [
            "```",
            "---",
            "End of README"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Fix common markdown issues
        cleaned = self._fix_markdown_formatting(cleaned)
        
        return cleaned
    
    def _fix_markdown_formatting(self, content: str) -> str:
        """Fix common markdown formatting issues."""
        # Ensure proper spacing around headers
        content = re.sub(r'\n(#+\s+[^\n]+)\n(?!\n)', r'\n\1\n\n', content)
        
        # Fix list formatting
        content = re.sub(r'\n(\s*[-*+]\s+[^\n]+)\n(?!\s*[-*+\n])', r'\n\1\n', content)
        
        # Ensure proper spacing around code blocks
        content = re.sub(r'\n(```[^\n]*\n.*?\n```)\n(?!\n)', r'\n\1\n\n', content, flags=re.DOTALL)
        
        # Remove excessive blank lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content
    
    def merge_responses(self, responses: List[str]) -> str:
        """Merge multiple LLM responses into a coherent README."""
        merged = ""
        
        for i, response in enumerate(responses):
            cleaned = self.clean_llm_response(response)
            
            if i == 0:
                # First response should contain the main structure
                merged = cleaned
            else:
                # Subsequent responses may contain additional sections
                # Try to intelligently merge them
                if "##" in cleaned:  # Contains headers
                    # Extract new sections
                    sections = re.split(r'\n(?=##\s)', cleaned)
                    for section in sections[1:]:  # Skip first empty split
                        if section.strip():
                            merged += f"\n\n## {section}"
                else:
                    # Just append as additional content
                    merged += f"\n\n{cleaned}"
        
        return self._fix_markdown_formatting(merged)
    
    def generate_readme(self, llm_responses: List[str], project_name: str, 
                       file_paths: List[str] = None) -> str:
        """Generate the final README content."""
        
        # Clean and merge LLM responses
        if len(llm_responses) == 1:
            main_content = self.clean_llm_response(llm_responses[0])
        else:
            main_content = self.merge_responses(llm_responses)
        
        # Ensure the README starts with a proper title
        if not main_content.startswith('#'):
            main_content = f"# {project_name}\n\n{main_content}"
        
        # Add generation timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = f"\n\n---\n*This README was generated by RepoWhisperer on {timestamp}*"
        
        final_readme = main_content + footer
        
        return self._fix_markdown_formatting(final_readme)
    
    def write_to_file(self, content: str, filepath: str):
        """Write README content to file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"README.md written successfully to {filepath}")
        except Exception as e:
            print(f"Error writing README to {filepath}: {e}")
            raise
    
    def validate_markdown(self, content: str) -> List[str]:
        """Validate markdown content and return list of issues."""
        issues = []
        
        # Check for basic structure
        if not content.strip():
            issues.append("Content is empty")
            return issues
        
        if not content.startswith('#'):
            issues.append("Missing main title (should start with #)")
        
        # Check for common formatting issues
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for malformed headers
            if line.startswith('#') and not line.startswith('# ') and len(line) > 1:
                if not re.match(r'^#+\s+', line):
                    issues.append(f"Line {i}: Malformed header - missing space after #")
            
            # Check for unclosed code blocks
            if line.strip() == '```':
                # Find matching closing block
                found_close = False
                for j in range(i, len(lines)):
                    if lines[j].strip() == '```':
                        found_close = True
                        break
                if not found_close:
                    issues.append(f"Line {i}: Unclosed code block")
        
        return issues
