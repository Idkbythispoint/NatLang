import os
import tkinter as tk
from tkinter import filedialog
from compile import parse_functions, generate_function_code
from openai import OpenAI

# Initialize OpenAI client
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

# Test the OpenAI client by listing models
try:
    model_list = client.models.list()
    models = list(model_list)
    for model in models:
        print(model.id)
except Exception as e:
    print(f"Error listing models: {e}")

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
    select_and_process_file()
