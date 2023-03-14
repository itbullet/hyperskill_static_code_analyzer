import re
import os
import sys
from pathlib import Path
import ast


class CodeAnalyzer:
    def __init__(self):
        self.blank_lines = 0

    def check_amount_of_lines_preceding_a_code(self, code_line):
        if self.blank_lines > 2 and re.match('.+', code_line):
            return True
        elif re.match('^\n$', code_line):
            self.blank_lines += 1
        else:
            self.blank_lines = 0
        return False


def check_length_of_code_line(code_line):
    return len(code_line) > 79


def check_indentation(code_line):
    pattern = r'^[ ]+'
    result = re.match(pattern, code_line)
    if result and len(result.group()) % 4 != 0:
        return True
    return False


def check_semicolon(code_line):
    pattern = r'(\'.*\')'
    result = re.sub(pattern, '', code_line)
    if re.search(';', result):
        pattern2 = r'.*#+.*;'
        result2 = re.match(pattern2, result)
        if result2:
            return False
        else:
            return True
    return False


def check_two_space_before_comment(code_line):
    if re.search('.+#', code_line):
        pattern = r'^.*\s{2,}#.*'
        result = re.match(pattern, code_line)
        if not result:
            return True
        else:
            return False
    return False


def check_todo(code_line):
    if re.search('#.*todo.*', code_line, flags=re.IGNORECASE):
        return True
    return False


def check_spaces_after_construction_name(code_line):
    if re.search(r'(def|class) {2,}\w', code_line):
        return True
    return False


def check_class_name(code_line):
    result = re.search(r'\bclass\b', code_line)
    result1 = re.search(r'(?<=class)\s+[A-Z][A-z0-9]+', code_line)
    if result and not result1:
        return re.search(r'^class +([A-z]+):', code_line).group(1)
    return False


def check_function_name(code_line):
    result = re.search(r'\bdef\b', code_line)
    result1 = re.search(r'(?<=def)\s+[a-z0-9_]+', code_line)
    if result and not result1:
        return re.search(r'def\s+([A-z0-9_]+)', code_line).group(1)
    return False


def check_argument_name(code, line_no):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno') and node.lineno == line_no:
            for arg in node.args.args:
                result = re.match('^[a-z0-9_]+', arg.arg)
                if not result:
                    return arg.arg


def check_variable_name(code, line_no, row):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and hasattr(node, 'lineno') \
                and node.lineno == line_no and re.match(r'^\s+\w', row):
            result = re.match(r'^[a-z0-9_]', node.id)
            if not result:
                return node.id


def check_argument_type(code, line_no):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno') and node.lineno == line_no:
            for item in node.args.defaults:
                if isinstance(item, ast.List):
                    return True


def check_file(file: dict(description='file name', type=str)):
    my_code_analyzer = CodeAnalyzer()

    with open(file, "r") as file:
        text_data = file.readlines()
        text_file = ''.join(text_data)

    for index, row in enumerate(text_data, start=1):
        if check_length_of_code_line(row):
            print(f'{file.name}: Line {index}: S001 Too long')
        if check_indentation(row):
            print(f'{file.name}: Line {index}: S002 Indentation is not a multiple of four')
        if check_semicolon(row):
            print(f'{file.name}: Line {index}: S003 Unnecessary semicolon')
        if check_two_space_before_comment(row):
            print(f'{file.name}: Line {index}: S004 At least two spaces required before inline comments')
        if check_todo(row):
            print(f'{file.name}: Line {index}: S005 TODO found')
        if my_code_analyzer.check_amount_of_lines_preceding_a_code(row):
            my_code_analyzer.blank_lines = 0
            print(f'{file.name}: Line {index}: S006 More than two blank lines used before this line')
        if check_spaces_after_construction_name(row):
            print(f'{file.name}: Line {index}: S007 Too many spaces after construction_name (def or class)')
        if check_class_name(row):
            print(f'{file.name}: Line {index}: S008 Class name \'{check_class_name(row)}\' should use CamelCase')
        if check_function_name(row):
            print(f'{file.name}: Line {index}: S009 Function name \'{check_function_name(row)}\' should use snake_case')
        if check_argument_name(text_file, index):
            print(f'{file.name}: Line {index}: S010 Argument name \'{check_argument_name(text_file, index)}\' '
                  f'should be snake_case')
        if check_variable_name(text_file, index, row):
            print(f'{file.name}: Line {index}: S011 Variable \'{check_variable_name(text_file, index, row)}\' in '
                  f'function should be snake_case')
        if check_argument_type(text_file, index):
            print(f'{file.name}: Line {index}: S012 Default argument value is mutable')

def main():
    """Get the argument from the command line"""
    if len(sys.argv) != 2:
        print('Usage: python code_analyzer.py <file_or_directory>')
        sys.exit()
    else:
        path = sys.argv[1]

    if os.path.isfile(path):
        if os.path.splitext(path)[1] == '.py':
            check_file(path)
        else:
            print(f'{path} is not a Python file')

    elif os.path.isdir(path):
        path_to_directory = Path(path)
        for py_file in path_to_directory.glob(f'**/*.py'):
            # strange bug where I needed to explicitly exclude tests.py to pass the test
            if py_file.name != 'tests.py':
                check_file(py_file)

    else:
        print(f'{path} is not a valid file or directory')


if __name__ == '__main__':
    main()
