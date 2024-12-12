import os
import tkinter as tk
from tkinter import filedialog
from compiler import parse_functions, generate_full_program
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
    # close the program if OpenAI is down
    exit()

def select_model(client):
    print("Select a model to use:")
    print("1. GPT-4o (gpt-4o)")
    print("2. GPT-4o-mini (gpt-4o-mini)")
    print("3. Custom")
    choice = input("Enter the number of your choice: ").strip()
    
    if choice == '1':
        return "gpt-4o"
    elif choice == '2':
        return "gpt-4o-mini"
    elif choice == '3':
        custom_model = input("Enter the custom model ID: ").strip()
        try:
            available_models = client.models.list()
            model_ids = [model.id for model in available_models]
            if custom_model in model_ids:
                return custom_model
            else:
                print("Invalid model ID. Please try again.")
                return select_model(client)
        except Exception as e:
            print(f"Error fetching model list: {e}")
            exit()
    else:
        print("Invalid choice. Please try again.")
        return select_model(client)

def select_and_process_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select file to parse", filetypes=[("Language Files", "*.lang"), ("All Files", "*.*")])
    if file_path:
        selected_model = select_model(client)
        print(f"Selected model: {selected_model}")
        functions, notes = parse_functions(file_path)  # Unpack functions and notes
        print("trying to open file selection 2")
        output_file = filedialog.asksaveasfilename(title="Save full program as", defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if output_file:
            full_program, errors = generate_full_program(functions, notes, selected_model)  # Pass selected_model
            with open(output_file, 'w') as f:
                f.write(full_program)
            print(f"Full program generated at {output_file}")
            if errors:
                errors_filename = f"{os.path.splitext(output_file)[0]}_errors.txt"
                with open(errors_filename, "w") as error_file:
                    error_file.write("\n".join(errors))
                print(f"Errors were encountered and could not be fixed automatically. See {errors_filename} for details.")

if __name__ == "__main__":
    select_and_process_file()
