import os
import re
from pydantic import BaseModel
from openai import OpenAI
import jedi
import logging
from typing import Optional

base_system_message = """
You are an AI assistant that converts function signatures into working Python code. 
Given a function signature, you will generate the complete function implementation in Python. 
Ensure that the generated code is syntactically correct and follows best practices. 
Include necessary imports and handle edge cases. Do not include any unnecessary code or comments.
The user input will always be a valid function signature.
Do NOT add TODOs or placeholders in the generated code.
Readability is not a concern. Focus on correctness and completeness.
The code should fully work how the user intended.
Unless specified otherwise, it should work all as one file, and start and work by just running it with Python.
If you have no notes to provide, you can leave the notes part of the response blank.
Here is the python code so far:
"""
current_system_message = base_system_message
class FunctionCode(BaseModel):
    code: str
    raised_exception: bool
    notes: str  # Removed Optional type

class CodeAnalysisResult(BaseModel):
    issues: list
    recommendations: list

class ErrorHandlingResult(BaseModel):
    fixed_code: str
    success: bool

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    logging.info(f"Parsing functions from {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Extract notes
    notes_pattern = r'!notes\[(.*?)\]'
    notes = re.findall(notes_pattern, content, re.DOTALL)
    
    # Extract functions
    func_pattern = r'(!func\s+name=\w+\[.*?\])'
    functions = re.findall(func_pattern, content, re.DOTALL)
    
    return functions, notes

def generate_function_code(function_signature, notes):
    logging.info(f"Generating code for signature: {function_signature}")
    try:
        messages = [
            {"role": "system", "content": current_system_message},
        ]
        if notes:
            messages.append({"role": "user", "content": "These are notes the user left:\n" + "\n".join(notes)})
        messages.append({"role": "user", "content": function_signature})
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=messages,
            response_format=FunctionCode,
            store=True,
            temperature=0.8,
            timeout=30  # Added timeout in seconds
        )
        generated_code = completion.choices[0].message.parsed.code
        generated_notes = completion.choices[0].message.parsed.notes
        if generated_code is None:
            return "print(Error during compilation! LLM did not return anything! Errored function signature: " + function_signature + ")", generated_notes
        return generated_code, generated_notes
    except TimeoutError:
        logging.error("API request timed out.")
        return "print(Error: API request timed out for function signature: " + function_signature + ")", None
    except Exception as e:
        print(f"Error during compilation!: {e}")
        return "print(Error during compilation! Errored function signature: " + function_signature + " Error: " + str(e) + ")", None

def refine_code(full_program, notes):
    logging.info("Refining the full program")
    refinement_message = """
    Please review the following Python code and fix any issues or improve its quality. 
    Ensure it follows best practices and is optimized for performance.
    Include necessary imports and handle edge cases. Do not include any unnecessary code or comments.
    Readability is not a concern. Focus on correctness and completeness.
    """
    try:
        messages = [
            {"role": "system", "content": refinement_message},
            {"role": "user", "content": full_program},
        ]
        if notes:
            messages.insert(1, {"role": "user", "content": "These are notes the user left:\n" + "\n".join(notes)})
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=messages,
            response_format=FunctionCode,
            store=True,
            temperature=0.7,
        )
        refined_code = completion.choices[0].message.parsed.code
        return refined_code if refined_code else full_program
    except Exception as e:
        print(f"Error during code refinement!: {e}")
        return full_program

def check_code(full_program, notes):
    logging.info("Checking the full program")
    check_message = """
    Please review the following Python code for any errors or improvements. 
    Ensure it follows best practices and is optimized for performance.
    Include necessary imports and handle edge cases. Do not include any unnecessary code or comments.
    Readability is not a concern. Focus on correctness and completeness.
    If the code is correct, and you can not spot any errors, respond with an empty message.
    """
    try:
        messages = [
            {"role": "system", "content": check_message},
            {"role": "user", "content": full_program},
        ]
        if notes:
            messages.insert(1, {"role": "user", "content": "These are notes the user left:\n" + "\n".join(notes)})
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=messages,
            response_format=FunctionCode,
            store=True,
            temperature=0.6,
        )
        checked_code = completion.choices[0].message.parsed.code
        if not checked_code:
            logging.info("Checker GPT returned empty response. Assuming code is fine.")
            return full_program
        return checked_code
    except Exception as e:
        print(f"Error during code checking!: {e}")
        return full_program

MAX_RETRIES = 3

def fix_errors(code, errors, notes, retries=0, max_retries=MAX_RETRIES):
    logging.info(f"Fixing errors: {errors} (Attempt {retries + 1})")
    error_fix_message = """
    You are an AI assistant specialized in fixing Python code errors.
    Given the following errors and code, provide a corrected version of the code.
    Ensure that all errors are resolved and the code follows best practices.
    Include necessary imports and handle edge cases. Do not include any unnecessary code or comments.
    Readability is not a concern. Focus on correctness and completeness.
    """
    try:
        messages = [
            {"role": "system", "content": error_fix_message},
            {"role": "user", "content": f"Errors:\n{errors}\n\nCode:\n{code}"},
        ]
        if notes:
            messages.insert(1, {"role": "user", "content": "These are notes the user left:\n" + "\n".join(notes)})
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06-error-fixer",
            messages=messages,
            response_format=ErrorHandlingResult,
            store=True,
            temperature=0.7,
            timeout=30  # Added timeout
        )
        fixed_code = completion.choices[0].message.parsed.fixed_code
        success = completion.choices[0].message.parsed.success
        if success:
            return fixed_code, []
        else:
            if retries < max_retries:
                return fix_errors(code, errors, notes, retries + 1, max_retries)
            else:
                return code, errors
    except TimeoutError:
        logging.error("API request for error fixing timed out.")
        if retries < max_retries:
            return fix_errors(code, errors, notes, retries + 1, max_retries)
        else:
            return code, errors
    except Exception as e:
        print(f"Error during error fixing!: {e}")
        if retries < max_retries:
            return fix_errors(code, errors, notes, retries + 1, max_retries)
        else:
            return code, errors

def analyze_code(full_program):
    logging.info("Analyzing code")
    try:
        script = jedi.Script(code=full_program)
        diagnostics = script.get_syntax_errors()
        issues = [diag.msg for diag in diagnostics]
        recommendations = ["Review issue: " + issue for issue in issues]
        return CodeAnalysisResult(issues=issues, recommendations=recommendations)
    except Exception as e:
        logging.error(f"Error during code analysis!: {e}")
        return CodeAnalysisResult(issues=[], recommendations=[])

def generate_full_program(function_signatures, notes):
    logging.info("Generating full program from function signatures")
    generated_functions = []
    all_notes = []
    for index, signature in enumerate(function_signatures, start=1):
        logging.info(f"Processing function {index}/{len(function_signatures)}: {signature}")
        code, func_notes = generate_function_code(signature, notes)
        if func_notes.strip():
            all_notes.append(func_notes)
        generated_functions.append(code)
    full_program = "\n\n".join(generated_functions)
    refined_program = refine_code(full_program, notes)
    checked_program = check_code(refined_program, notes)
    analyzed_program = analyze_code(checked_program)
    if analyzed_program.issues:
        logging.warning("Code Analysis Issues found:")
        for issue in analyzed_program.issues:
            logging.warning(f"- {issue}")
        fixed_code, residual_errors = fix_errors(checked_program, analyzed_program.issues, notes)
        if residual_errors:
            return fixed_code, residual_errors
        # Re-analyze the fixed code
        new_analysis = analyze_code(fixed_code)
        if new_analysis.issues:
            fixed_code, residual_errors = fix_errors(fixed_code, new_analysis.issues, notes)
            if residual_errors:
                return fixed_code, residual_errors
        return fixed_code, []
    if all_notes:
        program_name = os.path.splitext(os.path.basename(sys.argv[2]))[0]
        notes_file = f"{program_name}_notes.txt"
        with open(notes_file, 'w') as nf:
            nf.write("\n\n".join(all_notes))
        logging.info(f"Notes written to {notes_file}")
    return checked_program, []

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python compile.py <input_file> <output_file>")
    else:
        functions, notes = parse_functions(sys.argv[1])
        full_program, errors = generate_full_program(functions, notes)
        if errors:
            print(f"Errors encountered: {errors}")
        print(f"Full program generated.")