#!/bin/bash

echo "=== Sutra Frontend-Backend Integration Test ==="
echo "Testing all the reported issues..."
echo ""

BASE_URL="http://localhost:3001/api"
ADMIN_PRINCIPAL="eyJ1c2VySWQiOiJ2ZWRwcmFrYXNoLTAwMSIsInVzZXJEZXRhaWxzIjoidmVkcHJha2FzaC5tQG91dGxvb2suY29tIiwiaWRlbnRpdHlQcm92aWRlciI6ImF6dXJlQWN0aXZlRGlyZWN0b3J5IiwidXNlclJvbGVzIjpbImFkbWluIiwidXNlciJdfQ=="

echo "1. Testing admin role recognition for vedprakash.m@outlook.com"
ADMIN_ROLES=$(curl -s -H "x-ms-client-principal: $ADMIN_PRINCIPAL" "$BASE_URL/getroles")
echo "Admin roles response: $ADMIN_ROLES"
if echo "$ADMIN_ROLES" | grep -q '"admin"'; then
    echo "✅ Admin role correctly recognized"
else
    echo "❌ Admin role NOT recognized"
fi
echo ""

echo "2. Testing Collections API (Save Collection functionality)"
COLLECTIONS=$(curl -s -H "x-ms-client-principal: $ADMIN_PRINCIPAL" "$BASE_URL/collections")
echo "Collections response: $COLLECTIONS"
if echo "$COLLECTIONS" | grep -q '"collections"'; then
    echo "✅ Collections API working"
else
    echo "❌ Collections API failed"
fi
echo ""

echo "3. Testing Prompts API (Save Prompt functionality)"
PROMPTS=$(curl -s -H "x-ms-client-principal: $ADMIN_PRINCIPAL" "$BASE_URL/prompts")
echo "Prompts response: $PROMPTS"
if echo "$PROMPTS" | grep -q '"prompts"'; then
    echo "✅ Prompts API working"
else
    echo "❌ Prompts API failed"
fi
echo ""

echo "4. Testing Playbooks API (Save Playbook functionality)"
PLAYBOOKS=$(curl -s -H "x-ms-client-principal: $ADMIN_PRINCIPAL" "$BASE_URL/playbooks")
echo "Playbooks response: $PLAYBOOKS"
if echo "$PLAYBOOKS" | grep -q '"playbooks"'; then
    echo "✅ Playbooks API working"
else
    echo "❌ Playbooks API failed"
fi
echo ""

echo "5. Testing Integrations API (Admin Configuration)"
INTEGRATIONS=$(curl -s -H "x-ms-client-principal: $ADMIN_PRINCIPAL" "$BASE_URL/integrations")
echo "Integrations response: $INTEGRATIONS"
if echo "$INTEGRATIONS" | grep -q '"integrations"'; then
    echo "✅ Integrations API working"
else
    echo "❌ Integrations API failed"
fi
echo ""

echo "6. Testing Guest LLM API (Test AI Response)"
GUEST_LLM=$(curl -s -X POST -H "Content-Type: application/json" -d '{"prompt": "Hello test", "model": "gpt-3.5-turbo"}' "$BASE_URL/anonymous/llm")
echo "Guest LLM response: $GUEST_LLM"
if echo "$GUEST_LLM" | grep -q '"choices"'; then
    echo "✅ Guest LLM API working"
else
    echo "❌ Guest LLM API failed"
fi
echo ""

echo "7. Testing Save Collection (POST)"
NEW_COLLECTION=$(curl -s -X POST -H "Content-Type: application/json" -H "x-ms-client-principal: $ADMIN_PRINCIPAL" -d '{"name": "Test Collection", "description": "Test Description"}' "$BASE_URL/collections")
echo "New collection response: $NEW_COLLECTION"
if echo "$NEW_COLLECTION" | grep -q '"id"'; then
    echo "✅ Save Collection working"
else
    echo "❌ Save Collection failed"
fi
echo ""

echo "8. Testing Save Prompt (POST)"
NEW_PROMPT=$(curl -s -X POST -H "Content-Type: application/json" -H "x-ms-client-principal: $ADMIN_PRINCIPAL" -d '{"title": "Test Prompt", "content": "Test content", "category": "general"}' "$BASE_URL/prompts")
echo "New prompt response: $NEW_PROMPT"
if echo "$NEW_PROMPT" | grep -q '"id"'; then
    echo "✅ Save Prompt working"
else
    echo "❌ Save Prompt failed"
fi
echo ""

echo "=== Test Summary ==="
echo "All APIs tested. Check individual results above."
echo "If any are failing, check the backend logs and frontend console."
