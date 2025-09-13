import re
from parts import Label, StackableWire, StackableSwitch, GateAND, GateOR, GateNOT, Connector, Gyro, ShortStick, StackableButton
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
    
    '=',

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
        self._replacements = {}
        self._init_variable_name = '_INIT'
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
        code = re.sub(r'/.*?/', '', code, flags=re.DOTALL)
        
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
                expr = parse_or_nor_xor_xnor(tokens)
                if not tokens or tokens.pop(0) != ')':
                    raise Exception("Expected ')'")
                return expr
            
            elif token == 'not':
                operand = parse_primary(tokens)
                # This is the change: transform 'not A' into 'not (_INIT or A)'
                or_expression = [self._init_variable_name, 'or', operand]
                return ['not', or_expression]
            
            elif self._is_valid_identifier(token):
                return token
            else:
                raise Exception(f"Unexpected token '{token}'")

        # Precedence level 2: and, nand
        def parse_and_nand(tokens):
            left = parse_primary(tokens)
            while tokens and tokens[0] in ('and', 'nand'):
                op = tokens.pop(0)
                right = parse_primary(tokens)
                left = [left, op, right]
            return left

        # Precedence level 3: or, nor, xor, xnor
        def parse_or_nor_xor_xnor(tokens):
            left = parse_and_nand(tokens)
            while tokens and tokens[0] in ('or', 'nor', 'xor', 'xnor'):
                op = tokens.pop(0)
                right = parse_and_nand(tokens)
                left = [left, op, right]
            return left

        return parse_or_nor_xor_xnor(tokens)

    def _transform_complex_gates(self, expr_tree):
        if isinstance(expr_tree, str):
            return expr_tree # Base case: an identifier

        # Recursively transform operands first
        if len(expr_tree) == 2 and expr_tree[0] == 'not':
            operand = self._transform_complex_gates(expr_tree[1])
            return ['not', operand]

        if len(expr_tree) == 3:
            left = self._transform_complex_gates(expr_tree[0])
            op = expr_tree[1]
            right = self._transform_complex_gates(expr_tree[2])

            if op == 'nand':
                # A nand B -> not (A and B)
                return ['not', [left, 'and', right]]
            elif op == 'nor':
                # A nor B -> not (A or B)
                return ['not', [left, 'or', right]]
            elif op == 'xor':
                # A xor B -> (A and (not B)) or ((not A) and B)
                not_b = ['not', right]
                a_and_not_b = [left, 'and', not_b]
                not_a = ['not', left]
                not_a_and_b = [not_a, 'and', right]
                return [a_and_not_b, 'or', not_a_and_b]
            elif op == 'xnor':
                # A xnor B -> (A and B) or ((not A) and (not B))
                a_and_b = [left, 'and', right]
                not_a = ['not', left]
                not_b = ['not', right]
                not_a_and_not_b = [not_a, 'and', not_b]
                return [a_and_b, 'or', not_a_and_not_b]
            else: # and, or are fundamental gates
                return [left, op, right]

        return expr_tree
    
    def _getTemporaryVariableName(self):
        temp_name = f"_TMP{self._temp_counter}"
        self._temp_counter += 1
        return temp_name

    def _flatten_expr(self, expr):
        # expr is a nested list/tree of fundamental gates
        temp_vars = []
        def flatten(e):
            if isinstance(e, str):
                return e
            if isinstance(e, list):
                # Flatten nested 'not'
                if len(e) == 2 and e[0] == 'not':
                    operand = flatten(e[1])

                    temp_name = self._getTemporaryVariableName()
                    temp_vars.append((temp_name, ['not', operand]))
                    return temp_name
                # Flatten nested binary gates
                elif len(e) == 3 and e[1] in ('and', 'or'):
                    left = flatten(e[0])
                    op = e[1]
                    right = flatten(e[2])

                    temp_name = self._getTemporaryVariableName()
                    temp_vars.append((temp_name, [left, op, right]))
                    return temp_name
                # Unwrap single-element lists
                elif len(e) == 1:
                    return flatten(e[0])
            raise Exception("Invalid expression structure for flattening")
        final_var = flatten(expr)
        return final_var, temp_vars

    def _parse_variable_line(self, line: list, type: str):
        definer = line[0]
        actual_definer = definer
        original_definer = definer

        if type == 'output' and len(line) == 1:
            line.append('=')
            line.append(line[0])

        if self._replacements.get(definer):
            actual_definer = self._replacements[definer] 

        if self._variables.get(definer) or self._replacements.get(definer):
            temp_name = self._getTemporaryVariableName()

            self._replacements[definer] = temp_name
            definer = temp_name

        if line[1] != '=':
            raise Exception("Variable definition must start with '='")

        expression = []
        
        for i, item in enumerate(line[2:]):
            if item not in expression_keywords and not self._is_valid_identifier(item):
                raise Exception("Unknown token '" + item + "'")
            
            if item in self._replacements and item != original_definer:
                item = self._replacements[item]
            elif  item in self._replacements and item == original_definer:
                item = actual_definer

            expression.append(item)

        # Step 1: Parse the raw expression into a tree
        expr_tree_raw = self._parse_expression(expression.copy())

        # Step 2: Transform complex gates into fundamental ones
        expr_tree_fundamental = self._transform_complex_gates(expr_tree_raw)

        # Step 3: Flatten the fundamental tree into temporary variables
        final_var, temp_vars = self._flatten_expr(expr_tree_fundamental)
        
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
        self._variables[self._init_variable_name] = {
            'type': 'input',
            'value': None
        }
        variables = self._variables
        parsed = self._parse_statements(code)

        for line in parsed:
            definer = line[0]

            if definer == 'input' or definer == 'output':
                continue

            if line[1] != '=':
                raise Exception("Variable definition must start with '=' \n Line: " + ' '.join(line))
            
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

        platform_base_connector = Connector()
        platform_stick1, platform_stick2 = ShortStick(), ShortStick()

        platform_stick1.connect(platform_base_connector, ConnectionConstants.connector_front_cup)
        platform_stick2.connect(platform_base_connector, ConnectionConstants.connector_back_cup)

        platform_connector1, platform_connector2 = Connector(), Connector()
        platform_connector1.connect(platform_stick1, ConnectionConstants.short_stick_cup)
        platform_connector2.connect(platform_stick2, ConnectionConstants.short_stick_cup)

        platform_stick3 = ShortStick()
        platform_stick4 = ShortStick()

        gyro1 = Gyro()
        gyro1.connect(platform_base_connector, ConnectionConstants.connector_side_cup1)

        gyro2 = Gyro()
        gyro2.connect(platform_base_connector, ConnectionConstants.connector_side_cup2)

        gyro3 = Gyro()
        gyro3.connect(platform_connector1, ConnectionConstants.connector_top_cup)

        gyro4 = Gyro()
        gyro4.connect(platform_connector2, ConnectionConstants.connector_top_cup)

        platform_stick3.connect(platform_connector1, ConnectionConstants.connector_front_cup)
        platform_stick4.connect(platform_connector2, ConnectionConstants.connector_front_cup)

        platform_base_connector.compile(compile_stack)

        platform_stick1.compile(compile_stack)
        platform_stick2.compile(compile_stack)

        platform_connector1.compile(compile_stack)
        platform_connector2.compile(compile_stack)

        platform_stick3.compile(compile_stack)
        platform_stick4.compile(compile_stack)
        
        gyro1.compile(compile_stack)
        gyro2.compile(compile_stack)
        gyro3.compile(compile_stack)
        gyro4.compile(compile_stack)

        base_connector = Connector()

        base_connector.connect(platform_stick3, ConnectionConstants.short_stick_cup)
        base_connector.compile(compile_stack)

        gate_connectors = [base_connector]

        inputs = []
        outputs = []
        
        for variable_name, data in variables.items():
            variable_type = data['type']
            variable_value = data['value']

            if variable_type == 'input':
                label = Label(variable_name, -90)

                if variable_name == self._init_variable_name:
                    wire = StackableButton()
                else:
                    wire = StackableSwitch()
                
                wire.connect(label, ConnectionConstants.label_cup)

                data['wire'] = wire
                inputs.append(label)

            elif variable_type == 'variable' or variable_type == 'temp' or variable_type == 'output':
                gate = self._check_dict_matches(states, variable_value)
                wires = []
                
                if gate == None:
                    data['wire'] = variables.get(variable_value, {}).get('wire')

                    if variable_type == 'output':
                        output_wire = data['wire']
                        label = Label(variable_name, 90)
                        
                        output_wire.connect(label, ConnectionConstants.label_cup)
                        outputs.append(label)

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
                
                last_connector = gate_connectors[-1]
                last_connector_cups = [k for k, v in gate_connectors[-1].cups.items() if not v]
                last_connector_cups.remove(ConnectionConstants.connector_top_cup)

                if len(last_connector_cups) == 0:
                    last_connector = Connector(rotationZ=180)
                    last_connector.connect(gate_connectors[-1], ConnectionConstants.connector_top_cup)
                    last_connector.compile(compile_stack)

                    last_connector_cups = [k for k, v in last_connector.cups.items() if not v]
                    last_connector_cups.remove(ConnectionConstants.connector_top_cup)

                    gate_connectors.append(last_connector)

                gate_instance.connect(last_connector, last_connector_cups[0])
                gate_instance.compile(compile_stack)
                data['wire'] = output_wire

                if variable_type == 'output':
                    output_wire = data['wire']
                    label = Label(variable_name, 90)
                    
                    output_wire.connect(label, ConnectionConstants.label_cup)
                    outputs.append(label)

        last_connector = Connector()
        last_connector.connect(gate_connectors[-1], ConnectionConstants.connector_top_cup)
        last_connector.compile(compile_stack)

        connectors = [Connector()]
        connectors[0].connect(platform_stick4, ConnectionConstants.short_stick_cup)
        height = max(len(inputs), len(outputs)) * 2
        
        for _ in range(height):
            connector = Connector()
            connector.connect(connectors[-1], ConnectionConstants.connector_top_cup)

            connectors.append(connector)

        for i, input_label in enumerate(inputs):
            input_label.connect(connectors[i * 2], ConnectionConstants.connector_front_cup)

        for i, output_label in enumerate(outputs):
            output_label.connect(connectors[i * 2], ConnectionConstants.connector_back_cup)
        

        for connector in connectors:
            connector.compile(compile_stack)
        
        for i, input_label in enumerate(inputs):
            input_label.compile(compile_stack)

        for i, output_label in enumerate(outputs):
            output_label.compile(compile_stack)

        for variable_name, data in variables.items():
            if 'wire' in data and not data['wire'].__dict__.get('_compiled'):
                data['wire'].compile(compile_stack)