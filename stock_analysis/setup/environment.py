import sys

def is_in_colab():
    """
    Checks if the code is running in Google Colab.

    Returns:
        True if in Colab, False otherwise.
    """
    return 'google.colab' in sys.modules
