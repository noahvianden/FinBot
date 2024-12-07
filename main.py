import os

# Base directory
base_path = r"C:\Users\noahv\PycharmProjects\FinBot\VM\VM_Projects"

# Create directories with names from "110" to "250" in 10-step increments
for i in range(600, 1001, 100):
    folder_name = str(i)
    folder_path = os.path.join(base_path, folder_name)
    try:
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created directory: {folder_path}")
    except Exception as e:
        print(f"Error creating directory {folder_path}: {e}")
