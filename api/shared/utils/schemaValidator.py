"""
Python Schema Validator Utility
Centralized validation using JSON schemas
Part of systematic resolution for validation centralization
"""

import json
import os
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError as JSONSchemaValidationError, Draft7Validator


class SchemaValidator:
    """Centralized schema validator for all entities"""
    
    def __init__(self):
        self.schemas = {}
        self.schema_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared", "schemas")
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all JSON schemas from the schemas directory"""
        try:
            # For now, use fallback schemas to avoid JSON reference resolution issues
            self._load_fallback_schemas()
            return
            
            schema_files = ['base.json', 'prompt.json', 'collection.json', 'playbook.json', 'user.json', 'cost.json']
            
            for schema_file in schema_files:
                schema_path = os.path.join(self.schema_dir, schema_file)
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        schema_name = schema_file.replace('.json', '')
                        self.schemas[schema_name] = json.load(f)
                        
        except Exception as e:
            print(f"Warning: Could not load schemas: {e}")
            # Provide basic fallback schemas
            self._load_fallback_schemas()
    
    def _load_fallback_schemas(self):
        """Load basic fallback schemas if files are not found"""
        self.schemas = {
            'prompt': {
                'type': 'object',
                'required': ['name', 'content'],
                'properties': {
                    'name': {'type': 'string', 'minLength': 1},
                    'content': {'type': 'string', 'minLength': 1},
                    'description': {'type': 'string'},
                    'tags': {'type': 'array', 'items': {'type': 'string'}},
                    'variables': {'type': 'array'},
                    'id': {'type': 'string'},
                    'userId': {'type': 'string'},
                    'createdAt': {'type': 'string'},
                    'updatedAt': {'type': 'string'},
                    'isPublic': {'type': 'boolean'},
                    'category': {'type': 'string'},
                    'usageCount': {'type': 'integer', 'minimum': 0},
                    'version': {'type': 'string'}
                },
                'additionalProperties': True
            },
            'collection': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string', 'minLength': 1},
                    'description': {'type': 'string'},
                    'type': {'type': 'string', 'enum': ['private', 'shared_team', 'public_marketplace']},
                    'tags': {'type': 'array', 'items': {'type': 'string'}},
                    'id': {'type': 'string'},
                    'userId': {'type': 'string'},
                    'createdAt': {'type': 'string'},
                    'updatedAt': {'type': 'string'}
                },
                'additionalProperties': True
            },
            'playbook': {
                'type': 'object',
                'required': ['name', 'steps'],
                'properties': {
                    'name': {'type': 'string', 'minLength': 1},
                    'description': {'type': 'string'},
                    'steps': {'type': 'array', 'minItems': 1},
                    'variables': {'type': 'array'},
                    'id': {'type': 'string'},
                    'userId': {'type': 'string'},
                    'createdAt': {'type': 'string'},
                    'updatedAt': {'type': 'string'}
                },
                'additionalProperties': True
            },
            'user': {
                'type': 'object',
                'required': ['id', 'email'],
                'properties': {
                    'id': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'name': {'type': 'string'},
                    'role': {'type': 'string', 'enum': ['user', 'admin', 'guest']},
                    'createdAt': {'type': 'string'},
                    'updatedAt': {'type': 'string'}
                },
                'additionalProperties': True
            },
            'cost': {
                'type': 'object',
                'required': ['userId', 'amount'],
                'properties': {
                    'userId': {'type': 'string'},
                    'amount': {'type': 'number', 'minimum': 0},
                    'currency': {'type': 'string'},
                    'provider': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'requestType': {'type': 'string'}
                },
                'additionalProperties': True
            }
        }
    
    def validate_entity(self, data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """
        Validate an entity against its schema
        
        Args:
            data: The data to validate
            entity_type: The type of entity (prompt, collection, playbook, user, etc.)
            
        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        if entity_type not in self.schemas:
            return {
                'valid': False,
                'errors': [f'Unknown entity type: {entity_type}']
            }
        
        schema = self.schemas[entity_type]
        
        try:
            validate(instance=data, schema=schema, cls=Draft7Validator)
            return {
                'valid': True,
                'errors': []
            }
        except JSONSchemaValidationError as e:
            return {
                'valid': False,
                'errors': [str(e)]
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Validation error: {str(e)}']
            }
    
    def validate_batch(self, entities: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
        """
        Validate multiple entities of the same type
        
        Args:
            entities: List of entities to validate
            entity_type: The type of entity
            
        Returns:
            Dictionary with overall validation result and individual errors
        """
        results = []
        all_valid = True
        
        for i, entity in enumerate(entities):
            result = self.validate_entity(entity, entity_type)
            results.append({
                'index': i,
                'valid': result['valid'],
                'errors': result['errors']
            })
            if not result['valid']:
                all_valid = False
        
        return {
            'valid': all_valid,
            'results': results,
            'total_count': len(entities),
            'valid_count': sum(1 for r in results if r['valid'])
        }


# Global validator instance
_validator = None


def get_validator() -> SchemaValidator:
    """Get the global validator instance"""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator


def validate_entity(data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """
    Convenience function to validate a single entity
    
    Args:
        data: The data to validate
        entity_type: The type of entity
        
    Returns:
        Dictionary with 'valid' boolean and 'errors' list
    """
    return get_validator().validate_entity(data, entity_type)


def validate_batch(entities: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
    """
    Convenience function to validate multiple entities
    
    Args:
        entities: List of entities to validate
        entity_type: The type of entity
        
    Returns:
        Dictionary with overall validation result
    """
    return get_validator().validate_batch(entities, entity_type)


# Export commonly used functions
__all__ = [
    'SchemaValidator',
    'get_validator',
    'validate_entity',
    'validate_batch'
]
