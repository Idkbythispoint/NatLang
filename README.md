
# NatLang

NatLang is a simple programming language designed to generate fully functional Python code from high-level function signatures and optional notes. This README will guide you through the syntax, features, and best practices for working with NatLang.

## Key Features

- **Function Signature Parsing**: Define functions in a clear and consistent format.
- **Contextual Notes**: Provide additional context or instructions to enhance code generation (optional).
- **Automatic Code Generation**: The compiler produces complete Python code for each function signature.
- **Error Handling**: Built-in mechanisms to handle errors and refine the generated code.
- **Logging**: Detailed logs for debugging and troubleshooting.

---

## Syntax Guide

### Function Definition

A function in NatLang is defined using the following format:

```
!func name=<function_name>[
<Description of the function and its purpose.>
]
```

#### Example

To create a function that adds two numbers:

```
!func name=add[
Add two numbers and return the result.
]
```

### Adding Notes

Notes can be included at the top of the file to provide context or special instructions for the compiler. Use the following syntax:

```
!notes[<Your note here.>]
```

#### Example

For a calculator application:

```
!notes[This is a test file for a simple calculator application. Ensure all operations are handled correctly.]
```

> **Note**: The `!notes` directive is optional. If not provided, the compiler will proceed with just the function definitions.

---

## Best Practices

- **Be Descriptive**: Use clear and detailed descriptions in both notes and function signatures.
- **Keep It Concise**: Avoid unnecessary verbosity in notes or function descriptions.
- **Organize Effectively**: If using the `!notes` directive, include it at the top of your file followed by related functions.
- **Test Thoroughly**: Verify the generated Python code to ensure it meets your requirements.

---

## Advanced Usage

### Structuring Files

NatLang files can begin with an optional `!notes` directive, followed by one or more `!func` definitions. For example:

```
!notes[This program handles basic arithmetic operations.]

!func name=add[
Add two numbers and return the result.
]

!func name=subtract[
Subtract the second number from the first and return the result.
]

!func name=multiply[
Multiply two numbers and return the result.
]

!func name=divide[
Divide the first number by the second and return the result. Handle division by zero.
]
```

Or, if no notes are needed:

```
!func name=add[
Add two numbers and return the result.
]

!func name=subtract[
Subtract the second number from the first and return the result.
]
```

### Error Handling

If errors are encountered during compilation, the compiler will attempt to fix them automatically. If unresolved, it will provide details for manual correction.

---

## Example Program

### Input File (`example_program.lang`):

```
!notes[This program demonstrates basic arithmetic functions for a calculator.]

!func name=add[
Add two numbers and return the result.
]

!func name=subtract[
Subtract the second number from the first and return the result.
]

!func name=multiply[
Multiply two numbers and return the result.
]

!func name=divide[
Divide the first number by the second and return the result. Handle division by zero.
]
```

Or, without notes:

```
!func name=add[
Add two numbers and return the result.
]

!func name=subtract[
Subtract the second number from the first and return the result.
]
```

### Output File (`output.py`):

```python
# Auto-generated Python code

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    return a / b
```

---

## Contributing

We welcome contributions to NatLang! Please feel free to submit issues or pull requests on the GitHub repository to improve the language or its documentation.

---

## License

NatLang is released under the MIT License. See `LICENSE` for more details.


