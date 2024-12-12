import os
import re
import tkinter as tk
from tkinter import filedialog
from pydantic import BaseModel
from openai import OpenAI

class FunctionCode(BaseModel):
    code: str

client = OpenAI()

def parse_functions(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    pattern = r'(!func\s+name=\w+\[.*?\])'
    functions = re.findall(pattern, content, re.DOTALL)
    
    return functions

def generate_function_code(function_signature):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Generate Python code for the following function signature."},
            {"role": "user", "content": function_signature},
        ],
        response_format=FunctionCode,
    )
    return completion.choices[0].message.parsed.code

def select_and_process_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select file to parse", filetypes=[("Language Files", "*.lang"), ("All Files", "*.*")])
    if file_path:
        functions = parse_functions(file_path)
        functions_dir = os.path.join(os.path.dirname(file_path), "functions")
        os.makedirs(functions_dir, exist_ok=True)
        
        for idx, func in enumerate(functions, start=1):
            code = generate_function_code(func)
            func_filename = os.path.join(functions_dir, f"function_{idx}.func")
            with open(func_filename, 'w') as f:
                f.write(code)
        print(f"{len(functions)} functions have been processed and saved to the 'functions' folder.")

if __name__ == "__main__":
    if client.api_key is None:
        raise ValueError("OpenAI API key is missing. Please set it in the OPENAI_API_KEY environment variable.")
    select_and_process_file()