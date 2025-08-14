import os
import shutil

def clean_pycache(root_dir):
    """
    Recursively deletes __pycache__ directories and .pyc files
    from the specified root directory.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Delete __pycache__ directories
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            print(f"Deleting directory: {pycache_path}")
            shutil.rmtree(pycache_path)
            # Remove from dirnames so os.walk doesn't try to enter it
            dirnames.remove('__pycache__')

        # Delete .pyc files
        for filename in filenames:
            if filename.endswith('.pyc'):
                pyc_file_path = os.path.join(dirpath, filename)
                print(f"Deleting file: {pyc_file_path}")
                os.remove(pyc_file_path)

if __name__ == "__main__":
    
    project_root = os.getcwd() 

    print(f"Cleaning __pycache__ and .pyc files in: {project_root}")
    clean_pycache(project_root)
    print("Cleaning complete.")