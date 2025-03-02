#!/usr/bin/env python3
"""
Marshal Decoder
Specialized tool to decrypt/decode Python marshal data
Focuses on handling marshal.loads() byte strings
"""

import marshal
import sys
import os
import types
import dis
from io import StringIO
import traceback
import re
import time

# Default output file for successful decompilations
DEFAULT_SUCCESS_FILE = "test-decsuccess.py"

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print a cool banner for the tool."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════╗
║                                                               ║
║  {Colors.BLUE}███╗   ███╗ █████╗ ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     {Colors.CYAN}║
║  {Colors.BLUE}████╗ ████║██╔══██╗██╔══██╗██╔════╝██║  ██║██╔══██╗██║     {Colors.CYAN}║
║  {Colors.BLUE}██╔████╔██║███████║██████╔╝███████╗███████║███████║██║     {Colors.CYAN}║
║  {Colors.BLUE}██║╚██╔╝██║██╔══██║██╔══██╗╚════██║██╔══██║██╔══██║██║     {Colors.CYAN}║
║  {Colors.BLUE}██║ ╚═╝ ██║██║  ██║██║  ██║███████║██║  ██║██║  ██║███████╗{Colors.CYAN}║
║  {Colors.BLUE}╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝{Colors.CYAN}║
║                                                               ║
║  {Colors.GREEN}██████╗ ███████╗ ██████╗ ██████╗ ██████╗ ███████╗██████╗  {Colors.CYAN}║
║  {Colors.GREEN}██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗ {Colors.CYAN}║
║  {Colors.GREEN}██║  ██║█████╗  ██║     ██║   ██║██║  ██║█████╗  ██████╔╝ {Colors.CYAN}║
║  {Colors.GREEN}██║  ██║██╔══╝  ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗ {Colors.CYAN}║
║  {Colors.GREEN}██████╔╝███████╗╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║ {Colors.CYAN}║
║  {Colors.GREEN}╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ {Colors.CYAN}║
║                                                               ║
╚═══════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.YELLOW}{Colors.BOLD}         Python Marshal Decoder Tool
         Decrypt marshal.loads() byte strings{Colors.ENDC}
"""
    print(banner)

def read_file(filename):
    """Read the content of a file."""
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"{Colors.RED}Error reading file: {e}{Colors.ENDC}")
        return None

def read_text_file(filename):
    """Read the content of a text file to extract marshal data."""
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        try:
            with open(filename, 'r', encoding='latin-1', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"{Colors.RED}Error reading file: {e}{Colors.ENDC}")
            return None

def save_content(content, filename):
    """Save content to a file."""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"{Colors.GREEN}✅ Successfully saved to {filename}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Error saving file: {e}{Colors.ENDC}")
        return False

def extract_marshal_data_from_text(text_content):
    """Extract marshal byte data from Python code."""
    # Look for common patterns of marshal data in Python code
    patterns = [
        r"marshal\.loads\(b['\"]([^'\"]+)['\"]",  # marshal.loads(b'...')
        r"marshal\.loads\(b\"\"\"([^\"\"\"]+)\"\"\"",  # marshal.loads(b"""...""")
        r"marshal\.loads\(bytes\(([^)]+)\)\)",  # marshal.loads(bytes(...))
        r"exec\(marshal\.loads\(b['\"]([^'\"]+)['\"]",  # exec(marshal.loads(b'...'))
        r"exec\(marshal\.loads\(b\"\"\"([^\"\"\"]+)\"\"\"",  # exec(marshal.loads(b"""..."""))
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_content)
        if matches:
            print(f"{Colors.GREEN}✅ Found marshal data using pattern: {pattern}{Colors.ENDC}")
            # Return the first match for now
            return matches[0]
    
    print(f"{Colors.YELLOW}⚠️ Couldn't find marshal data using known patterns. Trying raw content...{Colors.ENDC}")
    # If no patterns match, return the raw content (it might be direct binary data)
    return text_content

def convert_string_to_bytes(byte_str):
    """Convert a string representation of bytes to actual bytes."""
    try:
        # If it's already bytes, return it
        if isinstance(byte_str, bytes):
            return byte_str
        
        # If it's an escape sequence string like '\xe3\x00\x00...'
        if '\\x' in byte_str:
            # Evaluate the string as Python code
            try:
                # This is safer than eval
                result = bytes(int(x, 16) for x in byte_str.replace('\\x', ' ').split())
                return result
            except Exception:
                # Try different approach
                return eval(f"b'{byte_str}'")
        
        # Try direct encoding
        return byte_str.encode('latin-1')
    
    except Exception as e:
        print(f"{Colors.RED}❌ Error converting string to bytes: {e}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Trying alternative conversion methods...{Colors.ENDC}")
        
        try:
            # Try to interpret as hex
            if all(c in '0123456789abcdefABCDEF\\x' for c in byte_str.strip()):
                cleaned = byte_str.replace('\\x', '')
                return bytes.fromhex(cleaned)
        except Exception:
            pass
            
        try:
            # Last resort - raw encoding
            return byte_str.encode('raw_unicode_escape')
        except Exception as e:
            print(f"{Colors.RED}❌ All conversion methods failed: {e}{Colors.ENDC}")
            return None

def unmarshal_object(data):
    """Unmarshal the object from binary data."""
    if isinstance(data, str):
        data = convert_string_to_bytes(data)
        
    if not data:
        return None
        
    try:
        return marshal.loads(data)
    except Exception as e:
        print(f"{Colors.RED}❌ Error unmarshalling data: {e}{Colors.ENDC}")
        
        # Try to fix common issues with marshal data
        try:
            print(f"{Colors.YELLOW}Trying to fix marshal data format...{Colors.ENDC}")
            # Sometimes data has extra characters at the beginning
            for i in range(min(20, len(data))):
                try:
                    obj = marshal.loads(data[i:])
                    print(f"{Colors.GREEN}✅ Successfully unmarshalled after skipping {i} bytes{Colors.ENDC}")
                    return obj
                except Exception:
                    pass
        except Exception:
            pass
            
        return None

def handle_lambda_and_nested_code(obj, depth=0):
    """
    Process lambdas and nested code objects recursively.
    Returns a string with the decompiled nested objects.
    """
    result = ""
    indent = "    " * depth
    
    if isinstance(obj, types.CodeType):
        result += f"{indent}# Nested code object found:\n"
        try:
            # Try to use uncompyle6 if available
            try:
                import uncompyle6
                output = StringIO()
                uncompyle6.code_deparse(obj, out=output)
                nested_code = output.getvalue()
                result += f"{indent}{nested_code.replace(chr(10), chr(10) + indent)}\n"
            except (ImportError, Exception) as e:
                # Fall back to disassembly
                output = StringIO()
                dis.dis(obj, file=output)
                nested_code = output.getvalue()
                result += f"{indent}'''\n{indent}{nested_code.replace(chr(10), chr(10) + indent)}\n{indent}'''\n"
        except Exception as e:
            result += f"{indent}# Failed to decompile nested code: {e}\n"
    
    # For container types, recursively process to find nested code objects
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            nested_result = handle_lambda_and_nested_code(item, depth+1)
            if nested_result:
                result += f"{indent}# Item {i} in container:\n{nested_result}\n"
    
    elif isinstance(obj, dict):
        for key, value in obj.items():
            key_str = repr(key)
            nested_result = handle_lambda_and_nested_code(value, depth+1)
            if nested_result:
                result += f"{indent}# Dictionary key {key_str}:\n{nested_result}\n"
    
    return result

def decompile_code(code_obj):
    """Decompile a code object to Python source code."""
    try:
        # Try to import uncompyle6
        try:
            import uncompyle6
        except ImportError:
            print(f"{Colors.YELLOW}⚠️ Warning: uncompyle6 is not installed. Installing...{Colors.ENDC}")
            os.system("pip install uncompyle6")
            try:
                import uncompyle6
            except ImportError:
                print(f"{Colors.RED}❌ Error: Failed to install uncompyle6. Continuing with disassembly only.{Colors.ENDC}")
                raise ImportError("uncompyle6 not available")
        
        output = StringIO()
        uncompyle6.code_deparse(code_obj, out=output)
        source_code = output.getvalue()
        
        # Look for nested code objects (lambdas, comprehensions, etc.)
        nested_objects = ""
        
        # Check co_consts for nested code objects
        for const in code_obj.co_consts:
            nested_result = handle_lambda_and_nested_code(const)
            if nested_result:
                nested_objects += nested_result
        
        if nested_objects:
            source_code += "\n\n# ===== Nested Code Objects =====\n" + nested_objects
            
        return source_code
    
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Warning: Could not fully decompile code: {e}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Falling back to disassembly...{Colors.ENDC}")
        
        output = StringIO()
        # Include more verbose information in the disassembly
        output.write(f"# Python Disassembly (failed to decompile)\n")
        output.write(f"# Error: {str(e)}\n\n")
        
        # Print code object metadata
        output.write(f"# Code Object Metadata:\n")
        output.write(f"# - File name: {code_obj.co_filename}\n")
        output.write(f"# - Function name: {code_obj.co_name}\n")
        output.write(f"# - Argument count: {code_obj.co_argcount}\n")
        output.write(f"# - Local variables: {code_obj.co_varnames}\n")
        output.write(f"# - Constants: {code_obj.co_consts}\n\n")
        
        # Disassemble
        dis.dis(code_obj, file=output)
        
        return output.getvalue()

def decrypt_marshal_from_file(file_path, output_file=None):
    """Main function to decrypt marshal data from a file."""
    if not output_file:
        output_file = DEFAULT_SUCCESS_FILE
    
    print(f"{Colors.CYAN}🔍 Processing file: {file_path}{Colors.ENDC}")
    
    # Check file extension
    if file_path.endswith('.py') or file_path.endswith('.pyw') or file_path.endswith('.txt'):
        # Text file - read and extract marshal data
        content = read_text_file(file_path)
        if not content:
            return False
            
        print(f"{Colors.CYAN}🔍 Searching for marshal data in text file...{Colors.ENDC}")
        marshal_data = extract_marshal_data_from_text(content)
    else:
        # Binary file - read directly
        marshal_data = read_file(file_path)
    
    if not marshal_data:
        print(f"{Colors.RED}❌ Could not extract marshal data from file.{Colors.ENDC}")
        return False
    
    # Unmarshal the data
    print(f"{Colors.CYAN}🔄 Unmarshalling data...{Colors.ENDC}")
    unmarshalled = unmarshal_object(marshal_data)
    
    if not unmarshalled:
        print(f"{Colors.RED}❌ Failed to unmarshal data.{Colors.ENDC}")
        return False
    
    print(f"{Colors.CYAN}📄 Unmarshalled object type: {type(unmarshalled)}{Colors.ENDC}")
    
    # If not a code object
    if not isinstance(unmarshalled, types.CodeType):
        print(f"{Colors.YELLOW}⚠️ Not a code object, cannot decompile.{Colors.ENDC}")
        obj_repr = repr(unmarshalled)
        # Save raw representation
        save_content(f"# Marshal Decoded Object (not a code object)\n# Type: {type(unmarshalled)}\n\n{obj_repr}", output_file)
        return True
    
    # Decompile the code object
    print(f"{Colors.CYAN}🔄 Attempting to decompile...{Colors.ENDC}")
    decompiled = decompile_code(unmarshalled)
    
    # Output the result
    success = save_content(decompiled, output_file)
    
    if success:
        preview_length = 400
        print(f"\n{Colors.GREEN}--- Decompiled Code Preview ---{Colors.ENDC}")
        print(decompiled[:preview_length] + (f"{Colors.YELLOW}...{Colors.ENDC}" if len(decompiled) > preview_length else ""))
        print(f"\n{Colors.GREEN}--- End of Preview ---{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Decompilation completed successfully!{Colors.ENDC}")
        return True
    
    return False

def decrypt_marshal_from_string(marshal_string, output_file=None):
    """Decrypt marshal data from a string."""
    if not output_file:
        output_file = DEFAULT_SUCCESS_FILE
    
    print(f"{Colors.CYAN}🔍 Processing marshal string...{Colors.ENDC}")
    
    # Unmarshal the data
    print(f"{Colors.CYAN}🔄 Unmarshalling data...{Colors.ENDC}")
    unmarshalled = unmarshal_object(marshal_string)
    
    if not unmarshalled:
        print(f"{Colors.RED}❌ Failed to unmarshal data.{Colors.ENDC}")
        return False
    
    print(f"{Colors.CYAN}📄 Unmarshalled object type: {type(unmarshalled)}{Colors.ENDC}")
    
    # If not a code object
    if not isinstance(unmarshalled, types.CodeType):
        print(f"{Colors.YELLOW}⚠️ Not a code object, cannot decompile.{Colors.ENDC}")
        obj_repr = repr(unmarshalled)
        # Save raw representation
        save_content(f"# Marshal Decoded Object (not a code object)\n# Type: {type(unmarshalled)}\n\n{obj_repr}", output_file)
        return True
    
    # Decompile the code object
    print(f"{Colors.CYAN}🔄 Attempting to decompile...{Colors.ENDC}")
    decompiled = decompile_code(unmarshalled)
    
    # Output the result
    success = save_content(decompiled, output_file)
    
    if success:
        preview_length = 400
        print(f"\n{Colors.GREEN}--- Decompiled Code Preview ---{Colors.ENDC}")
        print(decompiled[:preview_length] + (f"{Colors.YELLOW}...{Colors.ENDC}" if len(decompiled) > preview_length else ""))
        print(f"\n{Colors.GREEN}--- End of Preview ---{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Decompilation completed successfully!{Colors.ENDC}")
        return True
    
    return False

def get_input_choice():
    """Get user choice for input method."""
    while True:
        print(f"\n{Colors.CYAN}Select input method:{Colors.ENDC}")
        print(f"{Colors.CYAN}1. {Colors.ENDC}Enter marshal byte string directly")
        print(f"{Colors.CYAN}2. {Colors.ENDC}Enter file path containing marshal data")
        
        choice = input(f"\n{Colors.BOLD}Enter your choice [1-2]: {Colors.ENDC}")
        
        if choice in ['1', '2']:
            return int(choice)
        
        print(f"{Colors.RED}Invalid choice. Please try again.{Colors.ENDC}")

def get_marshal_string():
    """Get marshal byte string from user."""
    print(f"\n{Colors.CYAN}Enter marshal byte string (e.g. b'\\xe3\\x00\\x00...'):{Colors.ENDC}")
    print(f"{Colors.YELLOW}(Paste the string and press Enter when done){Colors.ENDC}")
    
    marshal_string = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
    
    # Remove outer quotes if present
    if marshal_string.startswith(('"', "'", 'b"', "b'")) and marshal_string.endswith(('"', "'")):
        if marshal_string.startswith('b'):
            marshal_string = marshal_string[2:-1]
        else:
            marshal_string = marshal_string[1:-1]
    
    return marshal_string

def get_file_path():
    """Get file path from user."""
    print(f"\n{Colors.CYAN}Enter file path containing marshal data:{Colors.ENDC}")
    
    file_path = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
    
    if not os.path.exists(file_path):
        print(f"{Colors.RED}❌ File does not exist. Please check the path.{Colors.ENDC}")
        return None
    
    return file_path

def main():
    clear_screen()
    print_banner()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}Marshal Decoder - Direct Decrypt{Colors.ENDC}")
    print(f"{Colors.CYAN}This tool will decrypt and decompile Python marshal data.{Colors.ENDC}")
    
    # Get input choice
    choice = get_input_choice()
    
    if choice == 1:
        # Get marshal string
        marshal_string = get_marshal_string()
        if marshal_string:
            output_file = DEFAULT_SUCCESS_FILE
            decrypt_marshal_from_string(marshal_string, output_file)
    else:
        # Get file path
        file_path = get_file_path()
        if file_path:
            output_file = DEFAULT_SUCCESS_FILE
            decrypt_marshal_from_file(file_path, output_file)
    
    print(f"\n{Colors.BOLD}Process completed. Results saved to {DEFAULT_SUCCESS_FILE}{Colors.ENDC}")
    input(f"\n{Colors.BOLD}Press Enter to exit...{Colors.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}An unexpected error occurred: {e}{Colors.ENDC}")
        traceback.print_exc()
