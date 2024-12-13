import os
import subprocess
import tkinter as tk
from tkinter import filedialog

def build_java_to_exe(java_file, output_exe):
    # Compile Java source code
    compile_command = ["javac", java_file]
    subprocess.run(compile_command, check=True)
    
    # Get the base name of the Java file
    base_name = os.path.splitext(os.path.basename(java_file))[0]
    class_file = base_name + ".class"
    
    # Create executable using Launch4j
    # Assuming launch4j is installed and configured
    config_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<launch4jConfig>
    <outfile>{output_exe}</outfile>
    <jar></jar>
    <dontWrapJar>true</dontWrapJar>
    <headerType>gui</headerType>
    <classPath>
        <mainClass>{base_name}</mainClass>
    </classPath>
    <jre>
        <path></path>
        <bundledJre64Bit>false</bundledJre64Bit>
        <minVersion>1.8.0</minVersion>
    </jre>
</launch4jConfig>
'''
    config_file = f"{base_name}_launch4j.xml"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    # Run Launch4j
    build_command = ["launch4j", config_file]
    subprocess.run(build_command, check=True)
    
    # Clean up temporary files
    os.remove(config_file)
    print(f"Executable created: {output_exe}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    java_file = filedialog.askopenfilename(title="Select Java file to build", filetypes=[("Java Files", "*.java")])
    if java_file:
        output_exe = filedialog.asksaveasfilename(title="Save executable as", defaultextension=".exe", filetypes=[("Executable Files", "*.exe")])
        if output_exe:
            try:
                build_java_to_exe(java_file, output_exe)
            except subprocess.CalledProcessError as e:
                print(f"Error during build process: {e}")