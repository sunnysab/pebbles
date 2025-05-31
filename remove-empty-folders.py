import os
import sys # Import sys module

def remove_empty_folders(path):
    """
    Removes all empty folders within the given path.
    """
    if not os.path.isdir(path):
        print(f"Error: {path} is not a valid directory.")
        return

    # Walk through the directory tree from bottom up
    for root, dirs, files in os.walk(path, topdown=False):
        for folder_name in dirs:
            folder_path = os.path.join(root, folder_name)
            try:
                if not os.listdir(folder_path):  # Check if the folder is empty
                    os.rmdir(folder_path)
                    print(f"Removed empty folder: {folder_path}")
            except OSError as e:
                print(f"Error removing folder {folder_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remove-empty-folders.py <path>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    remove_empty_folders(target_path)
