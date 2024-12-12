import os
import re
from pydantic import BaseModel
from openai import OpenAI

class FunctionCode(BaseModel):
    code: str

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
                {"role": "system", "content": "Generate Python code for the following function signature."},
                {"role": "user", "content": function_signature},
            ],
            response_format=FunctionCode,
        )
        if completion.choices[0].message.parsed.code is None:
            return "print(Error during compilation! LLM did not return anything! Errored function signature: " + function_signature + ")"
        return completion.choices[0].message.parsed.code
    except Exception as e:
        print(f"Error during compilation!: {e}")
        return "print(Error during compilation! Errored function signature: " + function_signature + " Error: " + str(e) + ")"