import subprocess
import sys

# List of required packages
packages = [
    "numpy",
    "pandas",
    "matplotlib",
    "scikit-learn",
    "tensorflow",
    "torch",
    "transformers",
    "sentence-transformers",
    "nltk",
    "finbert-embedding"
]

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Start the installation process
if __name__ == "__main__":
    for package in packages:
        try:
            print(f"Installing {package}...")
            install(package)
            print(f"{package} installed successfully!")
        except Exception as e:
            print(f"Failed to install {package}: {e}")
