import unittest
import os
import sys

# Add the root directory to sys.path to allow imports from core, shared, etc.
# This is important because the tests are in a subdirectory but need to import modules
# from the parent directory and its subdirectories (like core and shared).
current_dir = os.path.dirname(os.path.abspath(__file__))
# If test.py is in the root, current_dir is the root.
# If you move test.py into a subfolder (e.g., a 'scripts' folder),
# you might need to adjust this (e.g., os.path.dirname(current_dir) to get to the actual root).
# For now, assuming test.py is at the root of the project.
project_root = current_dir
sys.path.insert(0, project_root)


def build_dependencies():
    """
    Placeholder for any build steps or dependency checks.
    For now, it doesn't do anything, but you can expand it later
    if you have compilation steps or specific environment setups.
    """
    print("Checking/building dependencies (if any)...")
    # Example: os.system("pip install -r requirements.txt")
    # Example: os.system("make")
    print("Dependencies checked/built.")

def run_tests():
    """
    Discovers and runs all tests in the 'tests' directory.
    """
    print("Discovering and running tests...")
    # Create a TestLoader instance
    loader = unittest.TestLoader()

    # Define the directory where tests are located
    # Assuming 'test.py' is in the root and 'tests' is a subdirectory
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')

    # Discover all tests in the 'tests' directory
    # The pattern 'test_*.py' will find any file starting with 'test_'
    suite = loader.discover(start_dir=tests_dir, pattern='test_*.py')

    # Create a TextTestRunner instance
    # verbosity=2 provides more detailed output
    runner = unittest.TextTestRunner(verbosity=2)

    # Run the tests
    result = runner.run(suite)

    # Exit with an appropriate status code
    # 0 if all tests passed, 1 otherwise
    if result.wasSuccessful():
        print("All tests passed successfully!")
        return 0
    else:
        print("Some tests failed.")
        return 1

if __name__ == '__main__':
    build_dependencies()
    exit_code = run_tests()
    sys.exit(exit_code)
