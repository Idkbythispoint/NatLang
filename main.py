import os
import tkinter as tk
from tkinter import filedialog
from compilers.pycompiler import parse_functions, generate_full_program
from openai import OpenAI
# Import javacompiler
from compilers.javacompiler import parse_methods, generate_full_program as generate_java_program
from compilers.javabuilder import build_java_to_exe
import platform

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
    #for model in models:
       # print(model.id)
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
    # Add language selection
    print("Select the programming language:")
    print("1. Python")
    print("2. Java")
    language_choice = input("Enter the number of your choice: ").strip()

    if language_choice == '1':
        language = 'python'
    elif language_choice == '2':
        language = 'java'
    else:
        print("Invalid choice. Defaulting to Python.")
        language = 'python'

    # Add OS and display check for file selection
    if platform.system() != "Windows":
        while True:
            file_path = input("Enter the path to the file to parse: ").strip()
            if os.path.isfile(file_path):
                break
            else:
                print("Invalid file path. Please enter a valid file path.")
    else:
        try:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(title="Select file to parse", filetypes=[("Language Files", "*.lang"), ("All Files", "*.*")])
        except tk.TclError:
            print("No display available. Please enter the path to the file to parse.")
            while True:
                file_path = input("Enter the path to the file to parse: ").strip()
                if os.path.isfile(file_path):
                    break
                else:
                    print("Invalid file path. Please enter a valid file path.")
    
    if file_path:
        selected_model = select_model(client)
        print(f"Selected model: {selected_model}")
        
        if language == 'python':
            functions, notes = parse_functions(file_path)
            # Add OS and display check for save dialog
            if platform.system() != "Windows":
                while True:
                    output_input = input("Enter the path to save the full program (.py) or a directory: ").strip()
                    if os.path.isdir(output_input):
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        output_file = os.path.join(output_input, f"{base_name}.py")
                        break
                    else:
                        output_dir = os.path.dirname(output_input) or '.'
                        if os.path.isdir(output_dir):
                            output_file = output_input
                            break
                        else:
                            print("Invalid directory. Please enter a valid save location.")
            else:
                try:
                    output_file = filedialog.asksaveasfilename(title="Save full program as", defaultextension=".py", filetypes=[("Python Files", "*.py")])
                except tk.TclError:
                    print("No display available. Please enter the path to save the full program.")
                    while True:
                        output_input = input("Enter the path to save the full program (.py) or a directory: ").strip()
                        if os.path.isdir(output_input):
                            base_name = os.path.splitext(os.path.basename(file_path))[0]
                            output_file = os.path.join(output_input, f"{base_name}.py")
                            break
                        else:
                            output_dir = os.path.dirname(output_input) or '.'
                            if os.path.isdir(output_dir):
                                output_file = output_input
                                break
                            else:
                                print("Invalid directory. Please enter a valid save location.")
            if output_file:
                full_program, errors = generate_full_program(functions, notes, selected_model)
                with open(output_file, 'w') as f:
                    f.write(full_program)
                print(f"Full program generated at {output_file}")
                if errors:
                    errors_filename = f"{os.path.splitext(output_file)[0]}_errors.txt"
                    with open(errors_filename, "w") as error_file:
                        error_file.write("\n".join(errors))
                    print(f"Errors were encountered and could not be fixed automatically. See {errors_filename} for details.")
        elif language == 'java':
            methods, notes = parse_methods(file_path)
            # Change output file naming
            # Add OS and display check for save dialog
            if platform.system() != "Windows":
                while True:
                    output_input = input("Enter the path to save the executable (.exe) or a directory: ").strip()
                    if os.path.isdir(output_input):
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        output_file = os.path.join(output_input, f"{base_name}.exe")
                        break
                    else:
                        output_dir = os.path.dirname(output_input) or '.'
                        if os.path.isdir(output_dir):
                            output_file = output_input
                            break
                        else:
                            print("Invalid directory. Please enter a valid save location.")
            else:
                try:
                    output_file = filedialog.asksaveasfilename(title="Save executable as", defaultextension=".exe", filetypes=[("Executable Files", "*.exe")])
                except tk.TclError:
                    print("No display available. Please enter the path to save the executable.")
                    while True:
                        output_input = input("Enter the path to save the executable (.exe) or a directory: ").strip()
                        if os.path.isdir(output_input):
                            base_name = os.path.splitext(os.path.basename(file_path))[0]
                            output_file = os.path.join(output_input, f"{base_name}.exe")
                            break
                        else:
                            output_dir = os.path.dirname(output_input) or '.'
                            if os.path.isdir(output_dir):
                                output_file = output_input
                                break
                            else:
                                print("Invalid directory. Please enter a valid save location.")
            if output_file:
                java_file_name = os.path.splitext(output_file)[0] + "_src.java"
                full_program, errors = generate_java_program(methods, notes, selected_model)
                with open(java_file_name, 'w') as f:
                    f.write(full_program)
                print(f"Java source file generated at {java_file_name}")
                # Build the Java file into an EXE
                build_java_to_exe(java_file_name, output_file)
                print(f"Executable created at {output_file}")
                if errors:
                    errors_filename = f"{os.path.splitext(output_file)[0]}_errors.txt"
                    with open(errors_filename, "w") as error_file:
                        error_file.write("\n".join(errors))
                    print(f"Errors were encountered and could not be fixed automatically. See {errors_filename} for details.")

if __name__ == "__main__":
    select_and_process_file()
