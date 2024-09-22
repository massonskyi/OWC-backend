import os
import shutil


__all__ = ['delete_pycache_directories']

def delete_pycache_directories(directory: str):
    """
    Deletes all the directories in the specified directory that are named
    __pycache__.
    @param directory: The directory to search for __pycache__ directories.
    @return: None
    """
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)
                print(f"Deleted {dir_path}")


if __name__ == '__main__':
    print("Python cache directories deleted successfully.")
    # Replace 'backend' with the path to your backend directory
    delete_pycache_directories('../')
