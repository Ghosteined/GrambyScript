/**
 * This file is a JavaScript translation of the provided Python parser and parts system.
 * It combines 'parser.py' and 'parts.py' into a single ES6 module.
 */

// ===================================================================================
//
//  Translated from: parts.py
//
// ===================================================================================

/**
 * @typedef {import('./parser').BaseItem} HasCups - An object with a 'cups' property. (JSDoc equivalent of Protocol)
 */

/**
 * Constants for defining attachment points and cups on various parts.
 */
const ConnectionConstants = {
    wire_ball_attachment1: 1,
    wire_ball_attachment2: 3,

    gyro_attachement: 1,
    label_attachment: 2,
    label_cup: 1,

    short_stick_attachment: 2,
    short_stick_cup: 1,

    connector_bottom_attachment: 5,
    connector_top_cup: 4,
    connector_front_cup: 6,
    connector_back_cup: 3,
    connector_side_cup1: 2,
    connector_side_cup2: 1,

    gate_attachment: 4,
    tri_gate_output: 1,
    tri_gate_input1: 2,
    tri_gate_input2: 3,

    two_gate_output: 1,
    two_gate_input: 2,

    wire_cup1: 4,
    wire_cup2: 2,
};

/**
 * Manages the collection of compiled parts.
 */
class CompileStack {
    constructor() {
        this._stack = [];
        this._items = []; // For debugging or reference
    }

    /**
     * Appends a compiled item to the stack.
     * @param {Array} stackItem - The compiled data for the item.
     * @param {BaseItem} classItem - The instance of the item.
     * @returns {number} The new ID of the item (1-based index).
     */
    append(stackItem, classItem) {
        this._stack.push(stackItem);
        this._items.push(classItem);
        return this._stack.length;
    }

    /**
     * Finalizes the stack and returns a base64 encoded JSON string.
     * @returns {string} The encoded string.
     */
    terminate() {
        const jsonString = JSON.stringify(this._stack);
        // In a browser environment, btoa is available.
        // In Node.js, you would use: Buffer.from(jsonString).toString('base64');
        return btoa(jsonString);
    }
}

/**
 * The base class for all physical parts in the simulation.
 */
class BaseItem {
    // Static properties to be defined on subclasses
    static Attachments = {};
    static Cups = {};
    static Name = "";

    constructor() {
        this._id = -1;
        this._compiled = false;
        // Create instance copies of static properties
        this.attachments = { ...this.constructor.Attachments };
        this.cups = { ...this.constructor.Cups };
        this._positions = [];
    }

    _getEmptyAttachment() {
        for (const attachmentId in this.attachments) {
            if (this.attachments[attachmentId] === false) {
                return parseInt(attachmentId, 10);
            }
        }
        return -1;
    }

    /**
     * Connects this item to another item's cup.
     * @param {HasCups} element - The item to connect to.
     * @param {number} cup - The specific cup on the element to connect to.
     */
    connect(element, cup) {
        if (element.cups[cup] === true) {
            throw new Error(`Cup ${cup} is already used on ${element.constructor.Name}!`);
        }
        const attachment = this._getEmptyAttachment();
        if (attachment === -1) {
            throw new Error(`No empty attachment found on ${this.constructor.Name}!`);
        }

        this.attachments[attachment] = true;
        element.cups[cup] = true;

        this._positions.push([attachment, cup, element]);
    }

    /**
     * Compiles the item into a format for the stack.
     * @param {CompileStack} stack - The compile stack.
     */
    compile(stack) {
        if (this._compiled) return;
        this._compiled = true;

        for (const position of this._positions) {
            let element = position[2];
            if (typeof element === 'number') continue; // Already an ID
            if (element._id === -1) {
                throw new Error(`Uncompiled part connection: ${this.constructor.Name} depends on an uncompiled ${element.constructor.Name}.`);
            }
            position[2] = element._id;
        }

        const item = [
            this.constructor.Name,
            this._positions,
            [] // Placeholder for extra data
        ];

        this._id = stack.append(item, this);
    }
}

// --- Gates ---
class GateAND extends BaseItem {
    static Attachments = { [ConnectionConstants.gate_attachment]: false };
    static Cups = {
        [ConnectionConstants.tri_gate_output]: false,
        [ConnectionConstants.tri_gate_input1]: false,
        [ConnectionConstants.tri_gate_input2]: false,
    };
    static Name = "Gate-AND";
}

class GateOR extends BaseItem {
    static Attachments = { [ConnectionConstants.gate_attachment]: false };
    static Cups = {
        [ConnectionConstants.tri_gate_output]: false,
        [ConnectionConstants.tri_gate_input1]: false,
        [ConnectionConstants.tri_gate_input2]: false,
    };
    static Name = "Gate-OR";
}

class GateNOT extends BaseItem {
    static Attachments = { [ConnectionConstants.gate_attachment]: false };
    static Cups = {
        [ConnectionConstants.two_gate_output]: false,
        [ConnectionConstants.two_gate_input]: false,
    };
    static Name = "Gate-NOT";
}

// --- Base parts ---
class Connector extends BaseItem {
    static Attachments = { [ConnectionConstants.connector_bottom_attachment]: false };
    static Cups = {
        [ConnectionConstants.connector_top_cup]: false,
        [ConnectionConstants.connector_front_cup]: false,
        [ConnectionConstants.connector_back_cup]: false,
        [ConnectionConstants.connector_side_cup1]: false,
        [ConnectionConstants.connector_side_cup2]: false
    };
    static Name = "Connector";
}

class ShortStick extends BaseItem {
    static Attachments = { [ConnectionConstants.short_stick_attachment]: false };
    static Cups = { [ConnectionConstants.short_stick_cup]: false };
    static Name = "ShortStick";
}

class Gyro extends BaseItem {
    static Attachments = { [ConnectionConstants.gyro_attachement]: false };
    static Cups = {};
    static Name = "Gyro";

    compile(stack) {
        if (this._compiled) return;
        this._compiled = true;

        for (const position of this._positions) {
            let element = position[2];
            if (typeof element === 'number') continue;
            if (element._id === -1) {
                 throw new Error(`Uncompiled part connection: ${this.constructor.Name} depends on an uncompiled ${element.constructor.Name}.`);
            }
            position[2] = element._id;
        }

        const datas = { "Activated": true };
        const item = [this.constructor.Name, this._positions, datas];
        this._id = stack.append(item, this);
    }
}

class Label extends BaseItem {
    static Attachments = { [ConnectionConstants.label_attachment]: false };
    static Cups = { [ConnectionConstants.label_cup]: false };
    static Name = "InputSensor";

    constructor(text, rotationY = 0) {
        super();
        this._str = text;
        this._rotationY = rotationY;
    }

    compile(stack) {
        if (this._compiled) return;
        this._compiled = true;

        for (const position of this._positions) {
            let element = position[2];
            if (typeof element === 'number') continue;
            if (element._id === -1) {
                throw new Error(`Uncompiled part connection: ${this.constructor.Name} depends on an uncompiled ${element.constructor.Name}.`);
            }
            position[2] = element._id;
        }

        const datas = { "ActivationKey": this._str };
        if (this._rotationY !== 0) {
            datas["OrientationY"] = this._rotationY;
        }
        const item = [this.constructor.Name, this._positions, datas];
        this._id = stack.append(item, this);
    }
}

// --- Wire types ---
class Wire extends BaseItem {
    static Attachments = {
        [ConnectionConstants.wire_ball_attachment1]: false,
        [ConnectionConstants.wire_ball_attachment2]: false,
    };
    static Cups = {
        [ConnectionConstants.wire_cup1]: false,
        [ConnectionConstants.wire_cup2]: false,
    };
    static Name = "Wire";
}

class Switch extends Wire {
    static Attachments = {
        [ConnectionConstants.wire_ball_attachment1]: false,
        [ConnectionConstants.wire_ball_attachment2]: false
    };
    static Cups = {
        [ConnectionConstants.wire_cup2]: false,
    };
    static Name = "Switch";

    /**
     * Overrides the default attachment selection order.
     * For a Switch, the "base" is attachment 2, which should be used first.
     * @returns {number} The ID of the first available attachment in the preferred order.
     */
    _getEmptyAttachment() {
        // Preferred attachment order: attachment 2 (ID 3), then attachment 1 (ID 1).
        const preferredOrder = [
            ConnectionConstants.wire_ball_attachment2,
            ConnectionConstants.wire_ball_attachment1
        ];

        for (const attachmentId of preferredOrder) {
            // Check if this attachment is available in the instance's attachments map.
            if (this.attachments[attachmentId] === false) {
                return attachmentId;
            }
        }

        return -1; // No empty attachment found
    }
}


/**
 * A base class for wires that can be chained together automatically.
 * Not intended for direct use. Extend it via StackableWire or StackableSwitch.
 */
class StackableWireType extends BaseItem {
    constructor() {
        super();
        this._item_cls = null;
        this._base_cls = null;
        this._items = [];
    }

    _initialize(item_cls, base_cls) {
        this._item_cls = item_cls;
        this._base_cls = base_cls;
        
        this.cups = { ...this._item_cls.Cups };
        this.attachments = { ...this._item_cls.Attachments };
        this.name = this._base_cls.Name;
        
        this._items = [new this._base_cls()];
    }

    _getLatestItem() {
        for (const item of this._items) {
            const hasFreeAttachment = Object.values(item.attachments).some(used => !used);
            if (hasFreeAttachment) {
                return item;
            }
        }

        const last_item = this._items[this._items.length - 1];
        const free_cups = Object.keys(last_item.cups).filter(k => !last_item.cups[k]);
        if (free_cups.length === 0) {
            throw new Error(`Cannot extend stackable wire: no free cups on ${last_item.constructor.Name}.`);
        }

        const new_item = new this._item_cls();
        new_item.connect(last_item, parseInt(free_cups[0], 10));
        this._items.push(new_item);
        return new_item;
    }
    
    // The ID of a stackable wire is the ID of its "end" part.
    get _id() {
        const possible_ids = this._items
            .filter(item => item._id !== -1)
            .map(item => [item._id, Object.values(item.cups).filter(v => !v).length]);
            
        if (possible_ids.length === 0) return -1;
        
        possible_ids.sort((a, b) => b[1] - a[1]); // Sort by most free cups
        return possible_ids[0][0];
    }
    
    set _id(value) { /* Do nothing, matching Python behavior */ }
    
    connect(element, cup) {
        const latest_item = this._getLatestItem();
        latest_item.connect(element, cup);
    }

    compile(stack) {
        if (this._compiled) return;
        this._compiled = true;
        // Compile all internal parts in order
        for (const item of this._items) {
            item.compile(stack);
        }
    }
}

class StackableWire extends StackableWireType {
    constructor() {
        super();
        this._initialize(Wire, Wire);
    }
}

class StackableSwitch extends StackableWireType {
    constructor() {
        super();
        // The base is a Switch, subsequent links are Wires.
        this._initialize(Wire, Switch);
    }
}


// ===================================================================================
//
//  Translated from: parser.py
//
// ===================================================================================

const expression_keywords = [
    'and', 'or', 'not', 'nand', 'nor', 'xor', 'xnor',
    '(', ')'
];

const states = {
    'and': [3, [0, 2], GateAND],
    'or':  [3, [0, 2], GateOR],
    'not': [2, [1],   GateNOT]
};

/**
 * Parses a custom logic language and compiles it into a set of connectable parts.
 */
class Parser {
    constructor() {
        this._variables = {};
        this._replacements = {}; // Track variable overrides
        this._temp_counter = 0;
    }

    _check_dict_matches(d, strings) {
        const matches = strings.filter(key => key in d);
        if (matches.length > 1) {
            throw new Error(`Multiple matches found in dictionary keys: ${matches}`);
        }
        return matches.length === 1 ? d[matches[0]] : null;
    }

    _is_valid_identifier(s) {
        return /^[A-Z0-9_]+$/.test(s);
    }

    _parse_statements(code) {
        code = code.replace(/\/\*.*?\*\//gs, ''); // Remove block comments
        const segments = code.split(';');
        const result = [];
        const token_pattern = /[A-Za-z0-9_]+|[=()]/g;

        for (const segment of segments) {
            const trimmed = segment.trim();
            if (trimmed) {
                result.push(trimmed.match(token_pattern) || []);
            }
        }
        return result;
    }

    _parse_expression(tokens) {
        const parse_or_nor_xor_xnor = (tkns) => {
            let left = parse_and_nand(tkns);
            while (tkns.length > 0 && ['or', 'nor', 'xor', 'xnor'].includes(tkns[0])) {
                const op = tkns.shift();
                const right = parse_and_nand(tkns);
                left = [left, op, right];
            }
            return left;
        };

        const parse_and_nand = (tkns) => {
            let left = parse_primary(tkns);
            while (tkns.length > 0 && ['and', 'nand'].includes(tkns[0])) {
                const op = tkns.shift();
                const right = parse_primary(tkns);
                left = [left, op, right];
            }
            return left;
        };
        
        const parse_primary = (tkns) => {
            if (tkns.length === 0) throw new Error("Unexpected end of expression");
            
            const token = tkns.shift();
            if (token === '(') {
                const expr = parse_or_nor_xor_xnor(tkns);
                if (tkns.length === 0 || tkns.shift() !== ')') throw new Error("Expected ')'");
                return expr;
            } else if (token === 'not') {
                const operand = parse_primary(tkns);
                return ['not', operand];
            } else if (this._is_valid_identifier(token)) {
                return token;
            } else {
                throw new Error(`Unexpected token '${token}'`);
            }
        };

        return parse_or_nor_xor_xnor(tokens);
    }
    
    _transform_complex_gates(expr_tree) {
        if (typeof expr_tree === 'string') return expr_tree; // Identifier

        if (Array.isArray(expr_tree) && expr_tree.length === 2 && expr_tree[0] === 'not') {
            const operand = this._transform_complex_gates(expr_tree[1]);
            return ['not', operand];
        }

        if (Array.isArray(expr_tree) && expr_tree.length === 3) {
            const left = this._transform_complex_gates(expr_tree[0]);
            const op = expr_tree[1];
            const right = this._transform_complex_gates(expr_tree[2]);

            switch (op) {
                case 'nand': return ['not', [left, 'and', right]]; // A nand B -> not (A and B)
                case 'nor':  return ['not', [left, 'or', right]]; // A nor B -> not (A or B)
                case 'xor': { // A xor B -> (A and not B) or (not A and B)
                    const not_b = ['not', right];
                    const a_and_not_b = [left, 'and', not_b];
                    const not_a = ['not', left];
                    const not_a_and_b = [not_a, 'and', right];
                    return [a_and_not_b, 'or', not_a_and_b];
                }
                case 'xnor': { // A xnor B -> (A and B) or (not A and not B)
                    const a_and_b = [left, 'and', right];
                    const not_a = ['not', left];
                    const not_b = ['not', right];
                    const not_a_and_not_b = [not_a, 'and', not_b];
                    return [a_and_b, 'or', not_a_and_not_b];
                }
                default: // and, or
                    return [left, op, right];
            }
        }
        return expr_tree;
    }

    _flatten_expr(expr) {
        const temp_vars = [];
        const flatten = (e) => {
            if (typeof e === 'string') return e;
            if (Array.isArray(e)) {
                const temp_name = `_TMP${this._temp_counter++}`;
                if (e.length === 2 && e[0] === 'not') {
                    const operand = flatten(e[1]);
                    temp_vars.push([temp_name, ['not', operand]]);
                    return temp_name;
                } else if (e.length === 3 && ['and', 'or'].includes(e[1])) {
                    const left = flatten(e[0]);
                    const op = e[1];
                    const right = flatten(e[2]);
                    temp_vars.push([temp_name, [left, op, right]]);
                    return temp_name;
                } else if (e.length === 1) {
                    return flatten(e[0]);
                }
            }
            throw new Error("Invalid expression structure for flattening");
        }
        const final_var = flatten(expr);
        return [final_var, temp_vars];
    }
    
    _getTemporaryVariableName() {
        return `_TMP${this._temp_counter++}`;
    }

    _parse_variable_line(line, type) {
        let definer = line[0];
        let actual_definer = definer;
        let original_definer = definer;

        // Output without definition: output X -> output X = X
        if (type === 'output' && line.length === 1) {
            line.push('=');
            line.push(line[0]);
        }

        if (this._replacements[definer]) {
            actual_definer = this._replacements[definer];
        }

        if (this._variables[definer] || this._replacements[definer]) {
            // Variable override: create temp variable and update mapping
            const temp_name = this._getTemporaryVariableName();
            this._replacements[definer] = temp_name;
            definer = temp_name;
        }

        if (line[1] !== '=') throw new Error(`Variable definition for '${definer}' must start with '='`);

        const expression = [];
        for (let i = 2; i < line.length; i++) {
            let item = line[i];
            if (!expression_keywords.includes(item) && !this._is_valid_identifier(item)) {
                throw new Error(`Unknown token '${item}'`);
            }
            if (this._replacements[item] && item !== original_definer) {
                item = this._replacements[item];
            } else if (this._replacements[item] && item === original_definer) {
                item = actual_definer;
            }
            expression.push(item);
        }

        const expr_tree_raw = this._parse_expression([...expression]);
        const expr_tree_fundamental = this._transform_complex_gates(expr_tree_raw);
        const [final_var, temp_vars] = this._flatten_expr(expr_tree_fundamental);

        for (const [temp_name, temp_expr] of temp_vars) {
            this._variables[temp_name] = { type: 'temp', value: temp_expr };
        }
        this._variables[definer] = { type, value: final_var };
    }

    PreCompile(code) {
        this._variables = {};
        this._replacements = {};
        this._temp_counter = 0;

        const parsed = this._parse_statements(code);

        for (const line of parsed) {
            let definer = line[0];

            if (definer === 'input') {
                if (line.length !== 2) throw new Error("Input must be exactly one value");
                const varName = line[1];
                if (!this._is_valid_identifier(varName)) throw new Error("Variable names must contain only uppercase letters, digits, and underscores");
                this._variables[varName] = { type: 'input', value: null };
            } else if (definer === 'output') {
                // Output without definition support
                // If output X; -> output X = X
                // If output X = Y; -> output X = Y
                const outputLine = line.slice(1);
                this._parse_variable_line(outputLine, 'output');
            } else if (this._is_valid_identifier(definer)) {
                this._parse_variable_line(line, 'variable');
            } else {
                throw new Error(`Unknown token '${definer}' in line: ${line.join(' ')}`);
            }
        }

        return this._variables;
    }

    Compile(compile_stack) {
        const platform = {
            base_connector: new Connector(), stick1: new ShortStick(), stick2: new ShortStick(),
            connector1: new Connector(), connector2: new Connector(), stick3: new ShortStick(),
            stick4: new ShortStick(), gyro1: new Gyro(), gyro2: new Gyro(),
            gyro3: new Gyro(), gyro4: new Gyro()
        };

        platform.stick1.connect(platform.base_connector, ConnectionConstants.connector_front_cup);
        platform.stick2.connect(platform.base_connector, ConnectionConstants.connector_back_cup);
        platform.connector1.connect(platform.stick1, ConnectionConstants.short_stick_cup);
        platform.connector2.connect(platform.stick2, ConnectionConstants.short_stick_cup);
        platform.gyro1.connect(platform.base_connector, ConnectionConstants.connector_side_cup1);
        platform.gyro2.connect(platform.base_connector, ConnectionConstants.connector_side_cup2);
        platform.gyro3.connect(platform.connector1, ConnectionConstants.connector_top_cup);
        platform.gyro4.connect(platform.connector2, ConnectionConstants.connector_top_cup);
        platform.stick3.connect(platform.connector1, ConnectionConstants.connector_front_cup);
        platform.stick4.connect(platform.connector2, ConnectionConstants.connector_front_cup);

        Object.values(platform).forEach(p => p.compile(compile_stack));

        const base_connector = new Connector();
        base_connector.connect(platform.stick3, ConnectionConstants.short_stick_cup);
        base_connector.compile(compile_stack);

        const gate_connectors = [base_connector];
        const inputs = [], outputs = [];

        for (const [variable_name, data] of Object.entries(this._variables)) {
            if (data.type === 'input') {
                const label = new Label(variable_name, -90);
                data.wire = new StackableSwitch();
                data.wire.connect(label, ConnectionConstants.label_cup);
                inputs.push(label);
            } else if (['variable', 'temp', 'output'].includes(data.type)) {
                const gate_info = Array.isArray(data.value) ? this._check_dict_matches(states, data.value) : null;
                
                if (gate_info === null) { // Direct assignment: C = A
                    data.wire = this._variables[data.value]?.wire;
                    if (!data.wire) throw new Error(`Wire for variable ${data.value} not found when defining ${variable_name}`);
                } else { // It's a gate
                    const GateClass = gate_info[2];
                    const gate_instance = new GateClass();
                    data.wire = new StackableWire();

                    if (gate_info[0] === 2) { // NOT gate
                        const input_wire = this._variables[data.value[1]]?.wire;
                        if (!input_wire) throw new Error(`Wire not found for ${data.value[1]}`);
                        input_wire.connect(gate_instance, ConnectionConstants.two_gate_input);
                        data.wire.connect(gate_instance, ConnectionConstants.two_gate_output);
                    } else if (gate_info[0] === 3) { // AND, OR gates
                        const [in1, in2] = [this._variables[data.value[0]]?.wire, this._variables[data.value[2]]?.wire];
                        if (!in1 || !in2) throw new Error(`Input wire not found for gate ${data.value[1]}`);
                        in1.connect(gate_instance, ConnectionConstants.tri_gate_input1);
                        in2.connect(gate_instance, ConnectionConstants.tri_gate_input2);
                        data.wire.connect(gate_instance, ConnectionConstants.tri_gate_output);
                    }

                    let last_connector = gate_connectors[gate_connectors.length - 1];
                    let free_cups = Object.keys(last_connector.cups).filter(k => !last_connector.cups[k] && parseInt(k) !== ConnectionConstants.connector_top_cup);
                    
                    if (free_cups.length === 0) {
                        const new_connector = new Connector();
                        new_connector.connect(last_connector, ConnectionConstants.connector_top_cup);
                        new_connector.compile(compile_stack);
                        last_connector = new_connector;
                        gate_connectors.push(last_connector);
                        free_cups = Object.keys(last_connector.cups).filter(k => !last_connector.cups[k] && parseInt(k) !== ConnectionConstants.connector_top_cup);
                    }
                    
                    gate_instance.connect(last_connector, parseInt(free_cups[0], 10));
                    gate_instance.compile(compile_stack);
                }

                if (data.type === 'output') {
                    const label = new Label(variable_name, 90);
                    data.wire.connect(label, ConnectionConstants.label_cup);
                    outputs.push(label);
                }
            }
        }

        const last_gate_connector = new Connector();
        last_gate_connector.connect(gate_connectors[gate_connectors.length - 1], ConnectionConstants.connector_top_cup);
        last_gate_connector.compile(compile_stack);

        const io_connectors = [new Connector()];
        io_connectors[0].connect(platform.stick4, ConnectionConstants.short_stick_cup);
        const height = Math.max(inputs.length, outputs.length) * 2;
        for (let i = 0; i < height; i++) {
            const connector = new Connector();
            connector.connect(io_connectors[io_connectors.length - 1], ConnectionConstants.connector_top_cup);
            io_connectors.push(connector);
        }

        inputs.forEach((label, i) => label.connect(io_connectors[i * 2], ConnectionConstants.connector_front_cup));
        outputs.forEach((label, i) => label.connect(io_connectors[i * 2], ConnectionConstants.connector_back_cup));
        
        io_connectors.forEach(c => c.compile(compile_stack));
        inputs.forEach(l => l.compile(compile_stack));
        outputs.forEach(l => l.compile(compile_stack));

        Object.values(this._variables).forEach(data => {
            if (data.wire && !data.wire._compiled) {
                data.wire.compile(compile_stack);
            }
        });
    }
}

// Export all classes and constants for use in other modules.
export {
    Parser,
    CompileStack,
    ConnectionConstants,
    BaseItem,
    GateAND,
    GateOR,
    GateNOT,
    Connector,
    Gyro,
    ShortStick,
    Label,
    Wire,
    Switch,
    StackableWire,
    StackableSwitch,
};