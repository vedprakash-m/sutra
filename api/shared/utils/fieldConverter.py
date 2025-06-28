"""
Python Field Converter Utility
Converts between snake_case (backend) and camelCase (frontend) field names
Part of systematic resolution for data model consistency
"""

import re
from typing import Any, Dict, List, Union


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase string to snake_case"""
    # Insert an underscore before any capital letter that follows a lowercase letter
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    # Insert an underscore before any capital letter that follows a lowercase letter or number
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case string to camelCase"""
    components = snake_str.split('_')
    # First component stays lowercase, subsequent components are capitalized
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def convert_camel_to_snake(obj: Any) -> Any:
    """
    Recursively convert all keys in a dictionary from camelCase to snake_case
    
    Args:
        obj: Dictionary, list, or primitive value to convert
        
    Returns:
        Converted object with snake_case keys
    """
    if isinstance(obj, dict):
        converted = {}
        for key, value in obj.items():
            snake_key = to_snake_case(key) if isinstance(key, str) else key
            converted[snake_key] = convert_camel_to_snake(value)
        return converted
    elif isinstance(obj, list):
        return [convert_camel_to_snake(item) for item in obj]
    else:
        return obj


def convert_snake_to_camel(obj: Any) -> Any:
    """
    Recursively convert all keys in a dictionary from snake_case to camelCase
    
    Args:
        obj: Dictionary, list, or primitive value to convert
        
    Returns:
        Converted object with camelCase keys
    """
    if isinstance(obj, dict):
        converted = {}
        for key, value in obj.items():
            camel_key = to_camel_case(key) if isinstance(key, str) else key
            converted[camel_key] = convert_snake_to_camel(value)
        return converted
    elif isinstance(obj, list):
        return [convert_snake_to_camel(item) for item in obj]
    else:
        return obj


def batch_convert_requests(requests: List[Dict[str, Any]], to_format: str = "snake") -> List[Dict[str, Any]]:
    """
    Convert a batch of request objects
    
    Args:
        requests: List of request dictionaries to convert
        to_format: "snake" or "camel" - target format
        
    Returns:
        List of converted request objects
    """
    converter = convert_camel_to_snake if to_format == "snake" else convert_snake_to_camel
    return [converter(req) for req in requests]


def batch_convert_responses(responses: List[Dict[str, Any]], to_format: str = "camel") -> List[Dict[str, Any]]:
    """
    Convert a batch of response objects
    
    Args:
        responses: List of response dictionaries to convert
        to_format: "snake" or "camel" - target format
        
    Returns:
        List of converted response objects
    """
    converter = convert_camel_to_snake if to_format == "snake" else convert_snake_to_camel
    return [converter(resp) for resp in responses]


# Export commonly used functions
__all__ = [
    'to_snake_case',
    'to_camel_case', 
    'convert_camel_to_snake',
    'convert_snake_to_camel',
    'batch_convert_requests',
    'batch_convert_responses'
]
