"""
Shared models package for Sutra application.
Contains all data models and schemas used across the application.
"""

# Import all models from the models.py file in the parent directory
import os
import sys
import importlib.util

# Get the parent shared directory
parent_dir = os.path.dirname(os.path.dirname(__file__))

# Import everything from models.py
spec = importlib.util.spec_from_file_location("models", os.path.join(parent_dir, "models.py"))
models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_module)

# Re-export all classes from models.py
from typing import Any
globals().update({name: getattr(models_module, name) for name in dir(models_module) if not name.startswith('_')})

# Make this directory a Python package
__version__ = "1.0.0"
