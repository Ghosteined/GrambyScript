# Grambyscript

Grambyscript is a minimalistic logic programming language inspired by the game *Road to Gramby's*. It is designed for defining logic circuits using a strict, readable syntax.
You can try it out [Here](https://ghosteined.github.io/GrambyScript/Web/) !

---

## Rules

### General Syntax

- Every statement must end with a semicolon (`;`).
- Variable names must be **UPPERCASE** and contain only **letters**, **numbers**, and **underscores**.
- Variable names **CANNOT** be overridden; attempting to do so will result in an error.
- Outputs are variables, they cannot override another variable name and they need to be assigned a value.
- Lines can be written consecutively without affecting execution — spacing is only for readability.
- **Comments** are written between single slashes, like `/ this is a comment /`.
- **Parentheses** are allowed in logic expressions to control evaluation order.

---

## Keywords

### `input`

Declares a named input variable. It must not be assigned a value. The user sets its value externally.

```gramsby
input SWITCH;
input SENSOR_1;
````

### `output`

Declares a named output variable. The expression on the right defines its logic value.
Unlike to input, an output needs to be assigned a value.

```gramsby
input A;
input B;
output RESULT = A and B;
```

### Logic Gates

The following logic gates are available in expressions:

* `and`
* `or`
* `nand`
* `nor`
* `xor`
* `xnor`

These gates operate between variables or sub-expressions. Parentheses can be used to group logic.

```gramsby
input A;
input B;
input C;

TEMP = A and B;
output RESULT = TEMP xor C;
```

---

## Comments

Comments are placed between single forward slashes `/ like this /`. They can appear on a line by themselves or inline.

```gramsby
/ Declare inputs /
input A;
input B;

/ Combine them using AND /
output OUT = A and B; / OUT is true only if both A and B are true /
```

Everything between the opening `/` and the closing `/` is ignored.

---

## Example

```gramsby
/ Basic XOR logic example /
/ You can also use the xor gate /
input A;
input B;

TEMP1 = A and (not B); / A and not B /
TEMP2 = (not A) and B; / not A and B /

output RESULT = TEMP1 or TEMP2;
```

---

## Notes

* All intermediate variables must be explicitly defined before use.
* No implicit declarations — every used variable must appear in an `input`, `output`, or assignment.
* There are no other keywords or features beyond what's described.
* Errors will occur if:

  * You forget a semicolon
  * Use an undefined variable
  * Use lowercase or invalid characters in variable names