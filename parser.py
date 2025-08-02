import re

from parts import Label, StackableWire, StackableSwitch, GateAND, GateOR, GateNOT
from parts import CompileStack, ConnectionConstants

# Constants
expression_keywords = [
    'and',
    'or',
    'not',
    'nand',
    'nor',
    'xor',
    'xnor',
    
    '(',
    ')'
]

states = {
    'and': [
        3,
        [0, 2],
        GateAND
    ],
    'or': [
        3,
        [0, 2],
        GateOR
    ],
    'not': [
        2,
        [1],
        GateNOT
    ]
}

# Class
class Parser:
    def __init__(self):
        self._variables = {}
        self._temp_counter = 0

    def _check_dict_matches(self, d: dict, strings: list[str]):
        matches = [key for key in strings if key in d]

        if len(matches) > 1:
            raise ValueError(f"Multiple matches found in dictionary keys: {matches}")
        elif len(matches) == 1:
            return d[matches[0]]
        else:
            return None

    def _is_valid_identifier(self, s: str):
        return re.fullmatch(r'[A-Z0-9_]+', s) is not None

    def _parse_statements(self, code: str):
        code = re.sub(r'/.*?/', '', code)
        segments = code.split(';')
        result = []

        token_pattern = re.compile(r'[A-Za-z0-9_]+|[=()]')

        for segment in segments:
            tokens = token_pattern.findall(segment.strip())
            if tokens:
                result.append(tokens)

        return result

    # Recursive descent parser for expressions
    def _parse_expression(self, tokens):
        def parse_primary(tokens):
            if not tokens:
                raise Exception("Unexpected end of expression")
            
            token = tokens.pop(0)

            if token == '(':
                expr = parse_or(tokens)
                if not tokens or tokens.pop(0) != ')':
                    raise Exception("Expected ')'")
                return expr
            
            elif token == 'not':
                operand = parse_primary(tokens)
                return ['not', operand]
            
            elif self._is_valid_identifier(token):
                return token
            else:
                raise Exception(f"Unexpected token '{token}'")

        def parse_and(tokens):
            left = parse_primary(tokens)
            while tokens and tokens[0] == 'and':
                tokens.pop(0)
                right = parse_primary(tokens)
                left = [left, 'and', right]
            return left

        def parse_or(tokens):
            left = parse_and(tokens)
            while tokens and tokens[0] == 'or':
                tokens.pop(0)
                right = parse_and(tokens)
                left = [left, 'or', right]
            return left

        return parse_or(tokens)

    def _flatten_expr(self, expr):
        # expr is a nested list/tree
        temp_vars = []
        def flatten(e):
            if isinstance(e, str):
                return e
            if isinstance(e, list):
                # Flatten nested 'not'
                if len(e) == 2 and e[0] == 'not':
                    operand = flatten(e[1])
                    temp_name = f"_TMP{self._temp_counter}"
                    self._temp_counter += 1
                    temp_vars.append((temp_name, ['not', operand]))
                    return temp_name
                # Flatten nested binary gates
                elif len(e) == 3 and e[1] in ('and', 'or'):
                    left = flatten(e[0])
                    op = e[1]
                    right = flatten(e[2])
                    temp_name = f"_TMP{self._temp_counter}"
                    self._temp_counter += 1
                    temp_vars.append((temp_name, [left, op, right]))
                    return temp_name
                # Unwrap single-element lists
                elif len(e) == 1:
                    return flatten(e[0])
            raise Exception("Invalid expression structure")
        final_var = flatten(expr)
        return final_var, temp_vars

    def _parse_variable_line(self, line: list, type: str):
        definer = line[0]

        if self._variables.get(definer):
            raise Exception("Variable name is already used")

        if line[1] != '=':
            raise Exception("Variable names must contain only uppercase letters, digits, and underscores")

        expression = []
        for i, item in enumerate(line):
            if i < 2:
                continue
            if item not in expression_keywords and not self._is_valid_identifier(item):
                raise Exception("Unknown token '" + item + "'")
            expression.append(item)

        expr_tree = self._parse_expression(expression.copy())

        # Always flatten, even if simple
        final_var, temp_vars = self._flatten_expr(expr_tree)
        for temp_name, temp_expr in temp_vars:
            self._variables[temp_name] = {
                'type': 'temp',
                'value': temp_expr
            }
        self._variables[definer] = {
            'type': type,
            'value': final_var
        }

    def PreCompile(self, code: str):
        variables = self._variables
        parsed = self._parse_statements(code)

        for line in parsed:
            definer = line[0]

            if definer == 'input' or definer == 'output':
                continue

            if line[1] != '=':
                raise Exception("Variable definition must start with '='")
            
            definition = line[2:]
            

        for line in parsed:
            definer = line[0]
            

            if definer == 'input':
                if not len(line) == 2:
                    raise Exception("Input must be exactly one value")
                if not self._is_valid_identifier(line[1]):
                    raise Exception("Variable names must contain only uppercase letters, digits, and underscores")
                
                variables[line[1]] = {
                    'type': 'input',
                    'value': None
                }
                continue

            if definer == 'output':
                line.pop(0)
                self._parse_variable_line(line, 'output')
                continue

            if self._is_valid_identifier(definer):
                self._parse_variable_line(line, 'variable')
                continue

            raise Exception("Unknown token '" + definer + "'")
    

        return variables
    
    def Compile(self, compile_stack: CompileStack):
        variables = self._variables

        for variable_name, data in variables.items():
            variable_type = data['type']
            variable_value = data['value']

            if variable_type == 'input':
                label = Label(variable_name)

                wire = StackableSwitch()
                wire.connect(label, ConnectionConstants.label_cup)

                label.compile(compile_stack)
                data['wire'] = wire

            elif variable_type == 'variable' or variable_type == 'temp' or variable_type == 'output':
                gate = self._check_dict_matches(states, variable_value)
                wires = []
                
                if gate == None:
                    data['wire'] = variables.get(variable_value, {}).get('wire')

                    if variable_type == 'output':
                        output_wire = data['wire']
                        label = Label(variable_name)
                        
                        output_wire.connect(label, ConnectionConstants.label_cup)
                        label.compile(compile_stack)

                    continue

                if gate[0] == 2:
                    wires.append(variables.get(variable_value[1], {}).get('wire'))
                elif gate[0] == 3:
                    wires.append(variables.get(variable_value[0], {}).get('wire'))
                    wires.append(variables.get(variable_value[2], {}).get('wire'))
                
                gate_instance = None
                output_wire = None

                if gate[0] == 2:
                    gate_instance = gate[2]()
                    wires[0].connect(gate_instance, ConnectionConstants.two_gate_input)

                    output_wire = StackableWire()
                    output_wire.connect(gate_instance, ConnectionConstants.two_gate_output)

                elif gate[0] == 3:
                    gate_instance = gate[2]()
                    wires[0].connect(gate_instance, ConnectionConstants.tri_gate_input1)
                    wires[1].connect(gate_instance, ConnectionConstants.tri_gate_input2)

                    output_wire = StackableWire()
                    output_wire.connect(gate_instance, ConnectionConstants.tri_gate_output)
                
                gate_instance.compile(compile_stack)
                data['wire'] = output_wire

                if variable_type == 'output':
                    output_wire = data['wire']
                    label = Label(variable_name)
                    
                    output_wire.connect(label, ConnectionConstants.label_cup)
                    label.compile(compile_stack)

        for variable_name, data in variables.items():
            if 'wire' in data and not data['wire'].__dict__.get('_compiled'):
                data['wire'].compile(compile_stack)