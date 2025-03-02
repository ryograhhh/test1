#!/usr/bin/env python3
"""
Marshal File Decoder/Decompiler
This tool helps decode and decompile Python marshal files.
Works on Termux and other Python environments.
"""

import argparse
import marshal
import sys
import os
import types
import dis
from io import StringIO
import traceback
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

{Colors.YELLOW}{Colors.BOLD}        Python Marshal Decompiler & Decoder Tool
        Works with marshal, pyc, and pyo files
        Supports lambda functions and nested code{Colors.ENDC}
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

def unmarshal_object(data):
    """Unmarshal the object from binary data."""
    try:
        return marshal.loads(data)
    except Exception as e:
        print(f"{Colors.RED}❌ Error unmarshalling data: {e}{Colors.ENDC}")
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

def process_pyc_file(filename):
    """Process .pyc file which has marshal data after a header."""
    with open(filename, 'rb') as f:
        # Try multiple header sizes (for different Python versions)
        for header_size in [4, 8, 12, 16]:
            try:
                f.seek(header_size)
                data = f.read()
                # Try to unmarshal and see if it works
                try:
                    marshal.loads(data)
                    print(f"{Colors.GREEN}✅ Successfully detected PYC header size: {header_size} bytes{Colors.ENDC}")
                    return data
                except Exception:
                    continue
            except Exception:
                continue
        
        # If we reached here, try a brute force approach
        print(f"{Colors.YELLOW}⚠️ Warning: Could not automatically detect PYC header size{Colors.ENDC}")
        print(f"{Colors.YELLOW}Trying brute force approach...{Colors.ENDC}")
        
        f.seek(0)
        file_content = f.read()
        
        # Try to find marshal data by scanning through the file
        for i in range(0, min(100, len(file_content))):
            try:
                data = file_content[i:]
                marshal.loads(data)
                print(f"{Colors.GREEN}✅ Found marshal data at offset: {i}{Colors.ENDC}")
                return data
            except Exception:
                continue
    
    print(f"{Colors.RED}❌ Failed to find valid marshal data in the file{Colors.ENDC}")
    return None

def process_file(input_file, output_file=None, is_pyc=False, raw_mode=False, verbose=False):
    """Process a single file with the given options."""
    if not output_file:
        output_file = DEFAULT_SUCCESS_FILE
        
    print(f"{Colors.CYAN}🔍 Processing file: {input_file}{Colors.ENDC}")
    
    # Read and process the file
    data = read_file(input_file)
    if data is None:
        return False
    
    # If it's a pyc file, extract marshal data
    if is_pyc or input_file.endswith('.pyc') or input_file.endswith('.pyo'):
        print(f"{Colors.CYAN}🔄 Treating file as PYC/PYO format...{Colors.ENDC}")
        data = process_pyc_file(input_file)
        if data is None:
            return False
    
    # Unmarshal the data
    print(f"{Colors.CYAN}🔄 Unmarshalling data...{Colors.ENDC}")
    unmarshalled = unmarshal_object(data)
    if unmarshalled is None:
        return False
    
    if verbose:
        print(f"{Colors.CYAN}📄 Unmarshalled object type: {type(unmarshalled)}{Colors.ENDC}")
        print(f"{Colors.CYAN}📄 Co-names (if code object): {getattr(unmarshalled, 'co_names', 'N/A')}{Colors.ENDC}")
        print(f"{Colors.CYAN}📄 Co-varnames (if code object): {getattr(unmarshalled, 'co_varnames', 'N/A')}{Colors.ENDC}")
    
    # If raw is selected or if unmarshalled object is not a code object
    if raw_mode or not isinstance(unmarshalled, types.CodeType):
        print(f"{Colors.CYAN}📄 Unmarshalled object type: {type(unmarshalled)}{Colors.ENDC}")
        if not isinstance(unmarshalled, types.CodeType):
            print(f"{Colors.YELLOW}⚠️ Not a code object, cannot decompile.{Colors.ENDC}")
            print(f"{Colors.CYAN}📄 Object value (repr): {repr(unmarshalled)}{Colors.ENDC}")
            return False
    
    # Decompile the code object
    print(f"{Colors.CYAN}🔄 Attempting to decompile...{Colors.ENDC}")
    decompiled = decompile_code(unmarshalled)
    
    # Output the result
    success = save_content(decompiled, output_file)
    
    if success and (verbose or True):  # Always show a preview
        preview_length = 800 if verbose else 400
        print(f"\n{Colors.GREEN}--- Decompiled Code Preview ---{Colors.ENDC}")
        print(decompiled[:preview_length] + (f"{Colors.YELLOW}...{Colors.ENDC}" if len(decompiled) > preview_length else ""))
        print(f"\n{Colors.GREEN}--- End of Preview ---{Colors.ENDC}")
    
    if success:
        print(f"{Colors.GREEN}✅ Decompilation completed successfully!{Colors.ENDC}")
        return True
    return False

def get_file_path():
    """Get file path from user interactively."""
    while True:
        print(f"\n{Colors.CYAN}Enter the path to the marshal/pyc file to decompile:{Colors.ENDC}")
        print(f"{Colors.YELLOW}(Type 'back' to return to main menu){Colors.ENDC}")
        file_path = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
        
        if file_path.lower() == 'back':
            return None
            
        if not os.path.exists(file_path):
            print(f"{Colors.RED}❌ File does not exist. Please try again.{Colors.ENDC}")
            continue
            
        return file_path

def get_output_path(default_file=DEFAULT_SUCCESS_FILE):
    """Get output file path from user interactively."""
    print(f"\n{Colors.CYAN}Enter the output file path (press Enter for default: {default_file}):{Colors.ENDC}")
    output_path = input(f"{Colors.BOLD}> {Colors.ENDC}").strip()
    
    if not output_path:
        return default_file
    return output_path

def interactive_menu():
    """Interactive menu for the tool."""
    while True:
        clear_screen()
        print_banner()
        
        print(f"\n{Colors.BOLD}Select an option:{Colors.ENDC}")
        print(f"{Colors.CYAN}1. {Colors.ENDC}Decompile a Marshal/PYC file")
        print(f"{Colors.CYAN}2. {Colors.ENDC}Decompile with custom output file")
        print(f"{Colors.CYAN}3. {Colors.ENDC}Decompile with verbose output")
        print(f"{Colors.CYAN}4. {Colors.ENDC}Extract raw marshal data only")
        print(f"{Colors.CYAN}5. {Colors.ENDC}About this tool")
        print(f"{Colors.CYAN}6. {Colors.ENDC}Exit")
        
        choice = input(f"\n{Colors.BOLD}Enter your choice [1-6]: {Colors.ENDC}")
        
        if choice == '1':
            file_path = get_file_path()
            if file_path:
                process_file(file_path)
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '2':
            file_path = get_file_path()
            if file_path:
                output_path = get_output_path()
                process_file(file_path, output_path)
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '3':
            file_path = get_file_path()
            if file_path:
                output_path = get_output_path()
                process_file(file_path, output_path, verbose=True)
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '4':
            file_path = get_file_path()
            if file_path:
                process_file(file_path, raw_mode=True)
                input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '5':
            clear_screen()
            print_banner()
            print(f"\n{Colors.BOLD}About this tool:{Colors.ENDC}")
            print(f"""
{Colors.CYAN}This Marshal Decoder/Decompiler is designed to help you extract code
from Python marshal files, PYC files, and other compiled Python objects.

{Colors.GREEN}Features:{Colors.ENDC}
- Decompiles Python code objects back to source code
- Supports various Python versions
- Automatically detects PYC file headers
- Handles nested code objects and lambda functions
- Supports list/dict comprehensions
- Provides detailed code object metadata
- Works in Termux Android environment

{Colors.YELLOW}Limitations:{Colors.ENDC}
- Cannot fully decompile heavily obfuscated code
- Might produce incomplete results for newer Python versions
- Some complex constructs may not decompile perfectly

{Colors.BLUE}Created for educational and legitimate use only.{Colors.ENDC}
            """)
            input(f"\n{Colors.BOLD}Press Enter to return to main menu...{Colors.ENDC}")
        
        elif choice == '6':
            clear_screen()
            print(f"\n{Colors.GREEN}Thanks for using Marshal Decoder! Goodbye.{Colors.ENDC}")
            sys.exit(0)
        
        else:
            print(f"{Colors.RED}Invalid choice. Please try again.{Colors.ENDC}")
            time.sleep(1)

def main():
    # Check if running with command-line arguments
    if len(sys.argv) > 1:
        # Command-line mode
        parser = argparse.ArgumentParser(description="Decode/Decompile Marshal-encoded Python files")
        parser.add_argument("input_file", nargs='?', help="Marshal encoded file to decode")
        parser.add_argument("-o", "--output", help=f"Output file for decoded content (default: {DEFAULT_SUCCESS_FILE} on success)")
        parser.add_argument("--pyc", action="store_true", help="Treat input as a .pyc file")
        parser.add_argument("--raw", action="store_true", help="Just unmarshal, don't try to decompile")
        parser.add_argument("--verbose", "-v", action="store_true", help="Show more detailed information")
        parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive menu mode")
        
        args = parser.parse_args()
        
        if args.interactive or not args.input_file:
            interactive_menu()
        else:
            try:
                process_file(args.input_file, args.output, args.pyc, args.raw, args.verbose)
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.ENDC}")
                if args.verbose:
                    traceback.print_exc()
                sys.exit(1)
    else:
        # No arguments, run interactive mode
        interactive_menu()

if __name__ == "__main__":
    main()
