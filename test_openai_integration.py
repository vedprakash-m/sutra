#!/usr/bin/env python3

"""
Simple test script to validate OpenAI integration.
This script tests the new OpenAI provider without requiring pytest.
"""

import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared.llm_providers.openai_provider import OpenAIProvider
from api.shared.llm_providers.base_provider import TokenUsage, LLMResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSecretClient:
    """Mock Secret Client for testing without Azure Key Vault."""
    
    def __init__(self):
        self.secrets = {
            "openai-api-key": type('Secret', (), {"value": "test-api-key"})(),
            "openai-config": type('Secret', (), {"value": '{"budget_limit": 100.0, "priority": 1, "enabled": true, "default_model": "gpt-3.5-turbo"}'})()
        }
    
    def get_secret(self, secret_name: str):
        if secret_name in self.secrets:
            return self.secrets[secret_name]
        raise Exception(f"Secret {secret_name} not found")


async def test_openai_provider_initialization():
    """Test OpenAI provider initialization."""
    print("🧪 Testing OpenAI Provider Initialization...")
    
    provider = OpenAIProvider()
    mock_kv_client = MockSecretClient()
    
    # Test initialization
    result = await provider.initialize(mock_kv_client)
    
    if result:
        print("✅ OpenAI provider initialized successfully")
        print(f"   - Provider name: {provider.provider_name}")
        print(f"   - Default model: {provider.default_model}")
        print(f"   - Available models: {len(provider.get_models())}")
        print(f"   - Budget limit: ${provider.budget_limit}")
        return True
    else:
        print("❌ Failed to initialize OpenAI provider")
        return False


async def test_model_info():
    """Test model information retrieval."""
    print("\n🧪 Testing Model Information...")
    
    provider = OpenAIProvider()
    models = provider._get_available_models()
    
    print(f"✅ Found {len(models)} OpenAI models:")
    for name, model_info in models.items():
        print(f"   - {model_info.display_name} ({name})")
        print(f"     Max tokens: {model_info.max_tokens}")
        print(f"     Cost: ${model_info.cost_per_input_token}/1K input, ${model_info.cost_per_output_token}/1K output")
        print(f"     Capabilities: {[cap.value for cap in model_info.capabilities]}")
        print()
    
    return True


async def test_cost_estimation():
    """Test cost estimation functionality."""
    print("🧪 Testing Cost Estimation...")
    
    provider = OpenAIProvider()
    mock_kv_client = MockSecretClient()
    await provider.initialize(mock_kv_client)
    
    test_prompt = "Write a short story about a robot learning to paint."
    
    for model in ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]:
        cost = provider.estimate_cost(test_prompt, model, max_tokens=500)
        print(f"✅ Estimated cost for {model}: ${cost:.6f}")
    
    return True


async def test_status_reporting():
    """Test provider status reporting."""
    print("\n🧪 Testing Status Reporting...")
    
    provider = OpenAIProvider()
    mock_kv_client = MockSecretClient()
    await provider.initialize(mock_kv_client)
    
    status = provider.get_status()
    
    print("✅ Provider Status:")
    print(f"   - Name: {status['name']}")
    print(f"   - Provider: {status['provider']}")
    print(f"   - Enabled: {status['enabled']}")
    print(f"   - Initialized: {status['initialized']}")
    print(f"   - Budget: ${status['current_usage']:.2f} / ${status['budget_limit']:.2f}")
    print(f"   - Available: {status['available']}")
    print(f"   - Models: {len(status['models'])}")
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting OpenAI Provider Tests")
    print("=" * 50)
    
    tests = [
        test_openai_provider_initialization,
        test_model_info,
        test_cost_estimation,
        test_status_reporting
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! OpenAI integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
