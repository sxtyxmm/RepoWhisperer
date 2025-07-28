import os
import ast
import tokenize
import io
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re


class CodeStructure:
    """Represents the structure of a code file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports = []
        self.classes = []
        self.functions = []
        self.variables = []
        self.docstring = None
        self.raw_content = ""
        self.language = self._detect_language()
    
    def _detect_language(self) -> str:
        """Detect programming language from file extension."""
        ext = Path(self.filepath).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return lang_map.get(ext, 'text')


class ClassInfo:
    """Information about a class."""
    
    def __init__(self, name: str, line_number: int, docstring: Optional[str] = None):
        self.name = name
        self.line_number = line_number
        self.docstring = docstring
        self.methods = []
        self.base_classes = []


class FunctionInfo:
    """Information about a function."""
    
    def __init__(self, name: str, line_number: int, docstring: Optional[str] = None):
        self.name = name
        self.line_number = line_number
        self.docstring = docstring
        self.parameters = []
        self.return_annotation = None
        self.is_async = False
        self.decorators = []


class FileParser:
    """Parses source code files and extracts structural information."""
    
    def __init__(self, exclude_dirs: List[str], exclude_files: List[str], 
                 supported_extensions: List[str]):
        self.exclude_dirs = set(exclude_dirs)
        self.exclude_files = exclude_files
        self.supported_extensions = set(supported_extensions)
    
    def should_exclude_dir(self, dir_path: str) -> bool:
        """Check if directory should be excluded."""
        dir_name = os.path.basename(dir_path)
        return dir_name in self.exclude_dirs or dir_name.startswith('.')
    
    def should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded."""
        file_name = os.path.basename(file_path)
        file_ext = Path(file_path).suffix
        
        # Check exclude patterns
        for pattern in self.exclude_files:
            if pattern.startswith('*'):
                if file_name.endswith(pattern[1:]):
                    return True
            elif file_name == pattern:
                return True
        
        # Check if extension is supported
        return file_ext not in self.supported_extensions
    
    def walk_project(self, project_path: str) -> List[str]:
        """Walk through project directory and collect relevant files."""
        files = []
        
        for root, dirs, filenames in os.walk(project_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self.should_exclude_dir(os.path.join(root, d))]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if not self.should_exclude_file(file_path):
                    files.append(file_path)
        
        return sorted(files)
    
    def parse_file(self, file_path: str) -> CodeStructure:
        """Parse a single file and extract its structure."""
        structure = CodeStructure(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                structure.raw_content = content
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return structure
        
        # Parse based on language
        if structure.language == 'python':
            self._parse_python_file(structure, content)
        else:
            self._parse_generic_file(structure, content)
        
        return structure
    
    def _parse_python_file(self, structure: CodeStructure, content: str) -> None:
        """Parse Python file using AST."""
        try:
            tree = ast.parse(content)
            
            # Get module docstring
            if (tree.body and isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant) and 
                isinstance(tree.body[0].value.value, str)):
                structure.docstring = tree.body[0].value.value
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure.imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        structure.imports.append(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.ClassDef):
                    class_info = ClassInfo(
                        name=node.name,
                        line_number=node.lineno,
                        docstring=ast.get_docstring(node)
                    )
                    
                    # Get base classes
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            class_info.base_classes.append(base.id)
                    
                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = FunctionInfo(
                                name=item.name,
                                line_number=item.lineno,
                                docstring=ast.get_docstring(item)
                            )
                            method_info.is_async = isinstance(item, ast.AsyncFunctionDef)
                            
                            # Get parameters
                            for arg in item.args.args:
                                method_info.parameters.append(arg.arg)
                            
                            class_info.methods.append(method_info)
                    
                    structure.classes.append(class_info)
                
                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) 
                    if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
                ):
                    func_info = FunctionInfo(
                        name=node.name,
                        line_number=node.lineno,
                        docstring=ast.get_docstring(node)
                    )
                    func_info.is_async = isinstance(node, ast.AsyncFunctionDef)
                    
                    # Get parameters
                    for arg in node.args.args:
                        func_info.parameters.append(arg.arg)
                    
                    # Get decorators
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name):
                            func_info.decorators.append(decorator.id)
                    
                    structure.functions.append(func_info)
                
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            structure.variables.append(target.id)
        
        except SyntaxError as e:
            print(f"Syntax error parsing {structure.filepath}: {e}")
        except Exception as e:
            print(f"Error parsing Python file {structure.filepath}: {e}")
    
    def _parse_generic_file(self, structure: CodeStructure, content: str) -> None:
        """Parse non-Python files using regex patterns."""
        lines = content.split('\n')
        
        # Basic patterns for different languages
        if structure.language in ['javascript', 'typescript']:
            self._parse_js_ts_file(structure, content, lines)
        elif structure.language == 'java':
            self._parse_java_file(structure, content, lines)
        elif structure.language in ['c', 'cpp']:
            self._parse_c_cpp_file(structure, content, lines)
        
        # For other languages, just extract basic info
        self._extract_basic_info(structure, lines)
    
    def _parse_js_ts_file(self, structure: CodeStructure, content: str, lines: List[str]) -> None:
        """Parse JavaScript/TypeScript files."""
        import_pattern = r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
        require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
        function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)'
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        const_function_pattern = r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
        
        for i, line in enumerate(lines, 1):
            # Imports
            for pattern in [import_pattern, require_pattern]:
                matches = re.findall(pattern, line)
                structure.imports.extend(matches)
            
            # Functions
            for pattern in [function_pattern, const_function_pattern]:
                matches = re.findall(pattern, line)
                for match in matches:
                    func_info = FunctionInfo(match, i)
                    structure.functions.append(func_info)
            
            # Classes
            matches = re.findall(class_pattern, line)
            for match in matches:
                class_info = ClassInfo(match, i)
                structure.classes.append(class_info)
    
    def _parse_java_file(self, structure: CodeStructure, content: str, lines: List[str]) -> None:
        """Parse Java files."""
        import_pattern = r'import\s+([^;]+);'
        class_pattern = r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)'
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)'
        
        for i, line in enumerate(lines, 1):
            # Imports
            matches = re.findall(import_pattern, line)
            structure.imports.extend(matches)
            
            # Classes
            matches = re.findall(class_pattern, line)
            for match in matches:
                class_info = ClassInfo(match, i)
                structure.classes.append(class_info)
            
            # Methods (simplified)
            matches = re.findall(method_pattern, line)
            for match in matches:
                if match not in ['if', 'for', 'while', 'switch']:  # Filter out keywords
                    func_info = FunctionInfo(match, i)
                    structure.functions.append(func_info)
    
    def _parse_c_cpp_file(self, structure: CodeStructure, content: str, lines: List[str]) -> None:
        """Parse C/C++ files."""
        include_pattern = r'#include\s*[<"](.*)[>"]'
        function_pattern = r'(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{'
        class_pattern = r'class\s+(\w+)'
        
        for i, line in enumerate(lines, 1):
            # Includes
            matches = re.findall(include_pattern, line)
            structure.imports.extend(matches)
            
            # Functions
            matches = re.findall(function_pattern, line)
            for match in matches:
                if match not in ['if', 'for', 'while', 'switch']:
                    func_info = FunctionInfo(match, i)
                    structure.functions.append(func_info)
            
            # Classes (C++)
            matches = re.findall(class_pattern, line)
            for match in matches:
                class_info = ClassInfo(match, i)
                structure.classes.append(class_info)
    
    def _extract_basic_info(self, structure: CodeStructure, lines: List[str]) -> None:
        """Extract basic information for unsupported languages."""
        # Look for function-like patterns
        function_patterns = [
            r'def\s+(\w+)',  # Python style
            r'function\s+(\w+)',  # JavaScript style
            r'(\w+)\s*\([^)]*\)\s*\{',  # C-style
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in function_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    func_info = FunctionInfo(match, i)
                    structure.functions.append(func_info)
    
    def get_file_summary(self, structure: CodeStructure) -> Dict[str, Any]:
        """Get a summary of the file structure."""
        return {
            'filepath': structure.filepath,
            'language': structure.language,
            'docstring': structure.docstring,
            'imports_count': len(structure.imports),
            'classes_count': len(structure.classes),
            'functions_count': len(structure.functions),
            'variables_count': len(structure.variables),
            'lines_count': len(structure.raw_content.split('\n')),
            'size_bytes': len(structure.raw_content.encode('utf-8'))
        }
