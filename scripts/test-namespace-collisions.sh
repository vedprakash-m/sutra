#!/bin/bash

# Simple Backend Dependencies Test

echo "🐍 Simple Backend Dependencies Test"
echo "==================================="

cd api

# Test namespace collisions first
echo "🔍 Testing for namespace collisions..."
python -c "
import os
import sys

# Critical Python built-in modules that must not conflict
critical_modules = [
    'collections', 'os', 'sys', 'json', 'time', 'datetime', 'itertools', 
    'functools', 'operator', 'pathlib', 'urllib', 'http', 'email', 'calendar',
    'uuid', 'random', 'math', 'statistics', 'decimal', 'fractions',
    'logging', 'warnings', 'traceback', 'contextlib', 'abc', 'types',
    'copy', 'pickle', 'shelve', 'marshal', 'sqlite3', 'csv', 'configparser'
]

api_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and not d.startswith('__')]
conflicts = [d for d in api_dirs if d in critical_modules]

if conflicts:
    print(f'❌ CRITICAL: Namespace collision detected: {conflicts}')
    print('These API directories conflict with Python built-in modules!')
    sys.exit(1)
else:
    print('✅ No namespace collisions detected')

# Test critical imports with current directory in path (exact CI simulation)
sys.path.insert(0, '.')
try:
    from collections import deque, defaultdict
    import json
    import os as os_module
    print('✅ Critical imports work with current directory in path')
except ImportError as e:
    print(f'❌ CRITICAL: Import error with current directory in path: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Namespace collision test passed"
else
    echo "❌ Namespace collision test failed"
    exit 1
fi

echo ""
echo "✅ All tests passed!"
