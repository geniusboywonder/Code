import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to sys.path to allow importing modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the function to be tested
from stock_analysis.setup.environment import is_in_colab

class TestSetup(unittest.TestCase):

    @patch.dict('sys.modules', {'google.colab': MagicMock()})
    def test_is_in_colab_true(self):
        # Use patch.dict to simulate running in Colab
        self.assertTrue(is_in_colab())

    @patch.dict('sys.modules', {}, clear=True)
    def test_is_in_colab_false(self):
        # Use patch.dict to simulate NOT running in Colab
        self.assertFalse(is_in_colab())

if __name__ == '__main__':
    unittest.main()
