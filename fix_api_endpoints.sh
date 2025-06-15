#!/bin/bash

# Script to fix common issues in API endpoints

echo "Fixing API endpoint issues..."

# List of API directories
API_DIRS="admin_api integrations_api llm_execute_api playbooks_api"

for dir in $API_DIRS; do
    echo "Processing api/${dir}/__init__.py"
    
    # Fix imports
    sed -i '' 's/from \.\.shared\.database import get_cosmos_client/from ..shared.database import get_database_manager/g' "api/${dir}/__init__.py"
    
    # Fix handle_api_error calls
    sed -i '' 's/handle_api_error(e, logger)/handle_api_error(e)/g' "api/${dir}/__init__.py"
    
    # Replace get_cosmos_client() with get_database_manager()
    sed -i '' 's/client = get_cosmos_client()/db_manager = get_database_manager()/g' "api/${dir}/__init__.py"
    
    echo "Fixed api/${dir}/__init__.py"
done

echo "Done fixing API endpoints"
