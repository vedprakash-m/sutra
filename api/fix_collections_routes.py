#!/usr/bin/env python3
"""
Fix collections API test route parameters.
"""

def fix_collections_tests():
    """Fix collections tests with missing route parameters."""
    
    test_file = "/Users/vedprakashmishra/sutra/api/collections_api/collections_test.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Define specific fixes based on test patterns and expected routes
    fixes = [
        # GET /api/collections/{id} - get single collection
        {
            'find': 'req = create_auth_request(method="GET")\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["id"] == collection_id',
            'replace': 'req = create_auth_request(\n            method="GET",\n            route_params={"id": collection_id}\n        )\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert response_data["id"] == collection_id'
        },
        # GET /api/collections/{id} - not found case
        {
            'find': 'req = create_auth_request(method="GET")\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 404',
            'replace': 'req = create_auth_request(\n            method="GET",\n            route_params={"id": collection_id}\n        )\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 404'
        },
        # PUT /api/collections/{id} - update collection
        {
            'find': 'req = create_auth_request(method="PUT")\n\n            # Act\n            response = await collections_main(req)',
            'replace': 'req = create_auth_request(\n                method="PUT",\n                route_params={"id": collection_id},\n                body=update_data\n            )\n\n            # Act\n            response = await collections_main(req)'
        },
        # DELETE /api/collections/{id} - delete collection success
        {
            'find': 'req = create_auth_request(method="DELETE")\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "deleted successfully" in response_data["message"]',
            'replace': 'req = create_auth_request(\n            method="DELETE",\n            route_params={"id": collection_id}\n        )\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 200\n        response_data = json.loads(response.get_body())\n        assert "deleted successfully" in response_data["message"]'
        },
        # DELETE /api/collections/{id} - delete collection with prompts (conflict)
        {
            'find': 'req = create_auth_request(method="DELETE")\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 409',
            'replace': 'req = create_auth_request(\n            method="DELETE",\n            route_params={"id": collection_id}\n        )\n\n        # Act\n        response = await collections_main(req)\n\n        # Assert\n        assert response.status_code == 409'
        },
        # GET /api/collections/{id}/prompts - get collection prompts
        {
            'find': 'req = create_auth_request(method="GET")\n\n        # Mock the request URL to include /prompts',
            'replace': 'req = create_auth_request(\n            method="GET",\n            route_params={"id": collection_id}\n        )\n\n        # Mock the request URL to include /prompts'
        }
    ]
    
    # Apply fixes
    updated_content = content
    for fix in fixes:
        find_text = fix['find']
        replace_text = fix['replace']
        
        if find_text in updated_content:
            updated_content = updated_content.replace(find_text, replace_text)
            print(f"Applied fix for: {find_text[:40]}...")
        else:
            print(f"Could not find: {find_text[:40]}...")
    
    # Write updated content
    with open(test_file, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {test_file}")

if __name__ == "__main__":
    fix_collections_tests()
