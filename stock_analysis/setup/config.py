import sys
import os

# Add the project root to sys.path to allow importing modules
# This is needed to import modules from the stock_analysis package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)


from stock_analysis.setup.environment import is_in_colab

# Flag to indicate if using GPU accelerated pandas (cuDF)
USE_GPU_PANDAS = False

if is_in_colab():
    print("Running in Google Colab environment.")
    try:
        import cudf
        import cupy
        print("cuDF and CuPy imported successfully. Checking for GPU...")

        # Check for GPU availability
        if cupy.cuda.is_available():
            print("GPU is available and will be used with cuDF.")
            USE_GPU_PANDAS = True
            # You might want to set a default device here if you have multiple GPUs
            # cupy.cuda.Device(0).use()

        else:
            print("GPU not detected. Please ensure a GPU runtime is enabled in Colab (Runtime -> Change runtime type). Falling back to pandas.")
            # Still need to import pandas even if cudf import succeeded but no GPU
            import pandas as pd

    except ImportError:
        print("cuDF or CuPy not found. Please ensure they are installed in your Colab environment.")
        print("Falling back to pandas. Enable GPU runtime and install cuDF/CuPy for acceleration.")
        import pandas as pd

else:
    print("Not running in Google Colab environment. Using pandas.")
    import pandas as pd


# Define the appropriate pandas module to use
if USE_GPU_PANDAS:
    # When using cuDF, the module is `cudf`
    pd_module = cudf
    DataFrame = cudf.DataFrame
    Series = cudf.Series
    print("Using cuDF for DataFrame operations.")
else:
    # When using standard pandas, the module is `pandas`
    pd_module = pd
    DataFrame = pd.DataFrame
    Series = pd.Series
    print("Using pandas for DataFrame operations.")


# This file can also be used for other configuration settings later
"""
# The closing triple quotes were missing below this line.
"""
