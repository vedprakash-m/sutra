#!/bin/bash

# Fix all relative imports in Azure Functions
# This is the root cause of the CI/CD failure

set -e

echo "🔧 FIXING RELATIVE IMPORTS"
echo "=========================="
echo "Converting relative imports to absolute imports for Azure Functions compatibility"
echo ""

# Function to add sys.path manipulation and fix imports in a file
fix_file_imports() {
    local file="$1"
    echo "Fixing imports in: $file"

    # Create a temporary file
    local temp_file=$(mktemp)

    # Add sys.path manipulation after the standard imports
    awk '
    BEGIN { added_path = 0 }
    /^import |^from [^.]/  {
        print
        if (!added_path && NR > 1) {
            print ""
            print "import sys"
            print "import os"
            print ""
            print "# Add the root directory to Python path for proper imports"
            print "sys.path.append(os.path.join(os.path.dirname(__file__), \"..\"))"
            print ""
            added_path = 1
        }
        next
    }
    /^from \.\.shared/ {
        # Convert relative import to absolute
        gsub(/^from \.\.shared/, "from shared")
        print
        next
    }
    { print }
    ' "$file" > "$temp_file"

    # Replace the original file
    mv "$temp_file" "$file"
}

# Files to fix
files=(
    "api/admin_api/__init__.py"
    "api/collections_api/__init__.py"
    "api/integrations_api/__init__.py"
    "api/llm_execute_api/__init__.py"
    "api/playbooks_api/__init__.py"
    "api/prompts/__init__.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        fix_file_imports "$file"
        echo "✅ Fixed: $file"
    else
        echo "⚠️  Not found: $file"
    fi
done

echo ""
echo "✅ All imports fixed!"
echo ""
echo "Testing health function import..."

# Test if the health function can now be imported
cd api
python3 -c "
import sys
sys.path.append('.')
try:
    from health import main
    print('✅ Health function can be imported successfully')
except Exception as e:
    print(f'❌ Health function import still failing: {e}')
    import traceback
    traceback.print_exc()
"
