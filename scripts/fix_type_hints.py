#!/usr/bin/env python3
"""
Script to fix Python 3.10+ type hints for compatibility with Python 3.9
Converts `Type | None` to `Optional[Type]` and `Type1 | Type2` to `Union[Type1, Type2]`
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def fix_union_type_hints(content: str) -> Tuple[str, int]:
    """
    Fix union type hints in Python code.
    Returns the fixed content and the number of changes made.
    """
    changes = 0
    lines = content.split('\n')
    fixed_lines = []
    
    # Check if typing imports are needed
    needs_optional = False
    needs_union = False
    has_typing_import = False
    
    for line in lines:
        if 'from typing import' in line:
            has_typing_import = True
            break
    
    # First pass: detect what imports we need
    for line in lines:
        # Skip comments and strings
        if '#' in line:
            code_part = line.split('#')[0]
        else:
            code_part = line
            
        # Detect patterns
        if re.search(r':\s*\w+\s*\|\s*None', code_part) or re.search(r'->\s*\w+\s*\|\s*None', code_part):
            needs_optional = True
        if re.search(r':\s*\w+\s*\|\s*\w+', code_part) or re.search(r'->\s*\w+\s*\|\s*\w+', code_part):
            needs_union = True
    
    # Second pass: fix the code
    import_added = False
    for i, line in enumerate(lines):
        # Add imports after the first docstring or comment block
        if not import_added and has_typing_import and i > 0:
            if 'from typing import' in line:
                imports = []
                if 'Optional' not in line and needs_optional:
                    imports.append('Optional')
                if 'Union' not in line and needs_union:
                    imports.append('Union')
                
                if imports:
                    # Add to existing import
                    if line.rstrip().endswith(')'):
                        line = line.rstrip()[:-1] + ', ' + ', '.join(imports) + ')'
                    else:
                        line = line.rstrip() + ', ' + ', '.join(imports)
                    changes += 1
                import_added = True
        
        # Skip comments and strings for replacement
        if '#' in line:
            code_part = line.split('#')[0]
            comment_part = '#' + '#'.join(line.split('#')[1:])
        else:
            code_part = line
            comment_part = ''
        
        # Fix Type | None -> Optional[Type]
        pattern1 = r'(\w+)\s*\|\s*None'
        if re.search(pattern1, code_part):
            code_part = re.sub(pattern1, r'Optional[\1]', code_part)
            changes += 1
        
        # Fix Type1 | Type2 -> Union[Type1, Type2] (but not for None)
        pattern2 = r'(\w+)\s*\|\s*(\w+)(?!\s*\|)'
        matches = re.finditer(pattern2, code_part)
        for match in reversed(list(matches)):
            if match.group(2) != 'None':
                code_part = code_part[:match.start()] + f'Union[{match.group(1)}, {match.group(2)}]' + code_part[match.end():]
                changes += 1
        
        fixed_lines.append(code_part + comment_part)
    
    # Add typing import if needed and not present
    if not has_typing_import and (needs_optional or needs_union):
        imports = []
        if needs_optional:
            imports.append('Optional')
        if needs_union:
            imports.append('Union')
        
        # Find where to add the import (after module docstring)
        insert_index = 0
        in_docstring = False
        for i, line in enumerate(fixed_lines):
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
                if not in_docstring:
                    insert_index = i + 1
                    break
        
        fixed_lines.insert(insert_index, f'from typing import {", ".join(imports)}')
        changes += 1
    
    return '\n'.join(fixed_lines), changes

def process_file(filepath: Path) -> bool:
    """
    Process a single Python file.
    Returns True if changes were made.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed_content, changes = fix_union_type_hints(content)
        
        if changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ Fixed {filepath} ({changes} changes)")
            return True
        else:
            print(f"⏭️  No changes needed in {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all Python files in the umbra directory."""
    
    # Get the umbra directory
    umbra_dir = Path('/Users/silviocorreia/Documents/GitHub/UMBRA/umbra')
    
    if not umbra_dir.exists():
        print(f"❌ Directory not found: {umbra_dir}")
        return
    
    print("🔧 Fixing Python type hints for Python 3.9 compatibility...")
    print("=" * 60)
    
    # Find all Python files
    python_files = list(umbra_dir.rglob('*.py'))
    
    total_files = len(python_files)
    fixed_files = 0
    
    for py_file in python_files:
        if process_file(py_file):
            fixed_files += 1
    
    print("=" * 60)
    print(f"✅ Processed {total_files} files, fixed {fixed_files} files")
    
    # Test imports
    print("\n🧪 Testing imports...")
    os.system('cd /Users/silviocorreia/Documents/GitHub/UMBRA && python3 -c "from umbra.modules import general_chat_mcp; print(\'✅ Import test passed\')"')

if __name__ == '__main__':
    main()
