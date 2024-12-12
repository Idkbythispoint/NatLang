import os
import re
from pydantic import BaseModel
from openai import OpenAI
import jedi

base_system_message = """
You are an AI assistant that converts function signatures into working Python code. 
Given a function signature, you will generate the complete function implementation in Python. 
Ensure that the generated code is syntactically correct and follows best practices. 
Include necessary imports and handle edge cases. Do not include any unnecessary code or comments.
The user input will always be a valid function signature.
Here is the python code so far:
"""
current_system_message = base_system_message
class FunctionCode(BaseModel):
    code: str
    raised_exception: bool

class CodeAnalysisResult(BaseModel):
    issues: list
    recommendations: list

class ErrorHandlingResult(BaseModel):
    fixed_code: str
    success: bool

try:
    client = OpenAI()
except Exception as e:
    if os.path.exists("openai.key") and os.path.isfile("openai.key") and os.path.getsize("openai.key") > 0:
        with open("openai.key", "r") as f:
            api_key = f.read().strip()
        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Error: {e}")
    elif os.path.exists("openai.key") and os.path.isfile("openai.key") and os.path.getsize("openai.key") == 0:
        print("Error: OpenAI API key is missing. Please set it in the OPENAI_API_KEY environment variable OR put it in the 'openai.key' file.")
    elif not os.path.exists("openai.key"):
        api_key = input("Error: OpenAI API key is not set. Please enter your OpenAI API key: ").strip()
        with open("openai.key", "w") as f:
            f.write(api_key)
        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            print(f"Something went wrong!!!!!!! Either OpenAI is down or the code is messed up: {e}")

def parse_functions(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    pattern = r'(!func\s+name=\w+\[.*?\])'
    functions = re.findall(pattern, content, re.DOTALL)
    
    return functions

def generate_function_code(function_signature):
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": current_system_message},
                {"role": "user", "content": function_signature},
            ],
            response_format=FunctionCode,
            store=True,
            temperature=0.8,
        )
        if completion.choices[0].message.parsed.code is None:
            return "print(Error during compilation! LLM did not return anything! Errored function signature: " + function_signature + ")"
        return completion.choices[0].message.parsed.code
    except Exception as e:
        print(f"Error during compilation!: {e}")
        return "print(Error during compilation! Errored function signature: " + function_signature + " Error: " + str(e) + ")"

def refine_code(full_program):
    refinement_message = """
    Please review the following Python code and fix any issues or improve its quality. 
    Ensure it follows best practices and is optimized for performance.
    """
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": refinement_message},
                {"role": "user", "content": full_program},
            ],
            response_format=FunctionCode,
            store=True,
            temperature=0.7,
        )
        refined_code = completion.choices[0].message.parsed.code
        return refined_code if refined_code else full_program
    except Exception as e:
        print(f"Error during code refinement!: {e}")
        return full_program

def check_code(full_program):
    check_message = """
    Please review the following Python code for any errors or improvements. 
    Ensure it follows best practices and is optimized for performance.
    """
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": check_message},
                {"role": "user", "content": full_program},
            ],
            response_format=FunctionCode,
            store=True,
            temperature=0.6,
        )
        checked_code = completion.choices[0].message.parsed.code
        return checked_code if checked_code else full_program
    except Exception as e:
        print(f"Error during code checking!: {e}")
        return full_program

MAX_RETRIES = 3

def fix_errors(code, errors, retries=0, max_retries=MAX_RETRIES):
    error_fix_message = """
    You are an AI assistant specialized in fixing Python code errors.
    Given the following errors and code, provide a corrected version of the code.
    Ensure that all errors are resolved and the code follows best practices.
    """
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06-error-fixer",
            messages=[
                {"role": "system", "content": error_fix_message},
                {"role": "user", "content": f"Errors:\n{errors}\n\nCode:\n{code}"},
            ],
            response_format=ErrorHandlingResult,
            store=True,
            temperature=0.7,
        )
        fixed_code = completion.choices[0].message.parsed.fixed_code
        success = completion.choices[0].message.parsed.success
        if success:
            return fixed_code, []
        else:
            if retries < max_retries:
                return fix_errors(code, errors, retries + 1, max_retries)
            else:
                return code, errors
    except Exception as e:
        print(f"Error during error fixing!: {e}")
        if retries < max_retries:
            return fix_errors(code, errors, retries + 1, max_retries)
        else:
            return code, errors

def analyze_code(full_program):
    try:
        script = jedi.Script(code=full_program)
        diagnostics = script.get_annotations()
        issues = [diag.message for diag in diagnostics]
        recommendations = ["Review issue: " + issue for issue in issues]
        return CodeAnalysisResult(issues=issues, recommendations=recommendations)
    except Exception as e:
        print(f"Error during code analysis!: {e}")
        return CodeAnalysisResult(issues=[], recommendations=[])

def generate_full_program(function_signatures):
    generated_functions = []
    for signature in function_signatures:
        code = generate_function_code(signature)
        generated_functions.append(code)
    full_program = "\n\n".join(generated_functions)
    refined_program = refine_code(full_program)
    checked_program = check_code(refined_program)
    analyzed_program = analyze_code(checked_program)
    if analyzed_program.issues:
        print("Code Analysis Issues:")
        for issue in analyzed_program.issues:
            print(f"- {issue}")
        fixed_code, residual_errors = fix_errors(checked_program, analyzed_program.issues)
        if residual_errors:
            return fixed_code, residual_errors
        # Re-analyze the fixed code
        new_analysis = analyze_code(fixed_code)
        if new_analysis.issues:
            fixed_code, residual_errors = fix_errors(fixed_code, new_analysis.issues)
            if residual_errors:
                return fixed_code, residual_errors
        return fixed_code, []
    return checked_program, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python compile.py <input_file> <output_file>")
    else:
        functions = parse_functions(sys.argv[1])
        full_program, errors = generate_full_program(functions)
        if errors:
            print(f"Errors encountered: {errors}")
        print(f"Full program generated.")