#!/usr/bin/env python3

"""
Simple test script to validate Anthropic integration.
This script tests the new Anthropic provider without requiring pytest.
"""

import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared.llm_providers.anthropic_provider import AnthropicProvider
from api.shared.llm_providers.base_provider import TokenUsage, LLMResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSecretClient:
    """Mock Secret Client for testing without Azure Key Vault."""
    
    def __init__(self):
        self.secrets = {
            "anthropic-api-key": type('Secret', (), {"value": "test-api-key"})(),
            "anthropic-config": type('Secret', (), {"value": '{"budget_limit": 100.0, "priority": 1, "enabled": true, "default_model": "claude-3-5-sonnet-20241022"}'})()
        }
    
    def get_secret(self, secret_name: str):
        if secret_name in self.secrets:
            return self.secrets[secret_name]
        raise Exception(f"Secret {secret_name} not found")


async def test_anthropic_provider_initialization():
    """Test Anthropic provider initialization."""
    print("🧪 Testing Anthropic Provider Initialization...")
    
    provider = AnthropicProvider()
    mock_kv_client = MockSecretClient()
    
    # Test initialization
    result = await provider.initialize(mock_kv_client)
    
    if result:
        print("✅ Anthropic provider initialized successfully")
        print(f"   - Provider name: {provider.provider_name}")
        print(f"   - Default model: {provider.default_model}")
        print(f"   - Available models: {len(provider.get_models())}")
        print(f"   - Budget limit: ${provider.budget_limit}")
        return True
    else:
        print("❌ Failed to initialize Anthropic provider")
        return False


async def test_model_info():
    """Test model information retrieval."""
    print("\n🧪 Testing Anthropic Model Information...")
    
    provider = AnthropicProvider()
    models = provider._get_available_models()
    
    print(f"✅ Found {len(models)} Anthropic models:")
    for name, model_info in models.items():
        print(f"   - {model_info.display_name} ({name})")
        print(f"     Max tokens: {model_info.max_tokens}")
        print(f"     Cost: ${model_info.cost_per_input_token}/1K input, ${model_info.cost_per_output_token}/1K output")
        print(f"     Capabilities: {[cap.value for cap in model_info.capabilities]}")
        print(f"     Context window: {model_info.context_window:,} tokens")
        print()
    
    return True


async def test_cost_estimation():
    """Test cost estimation functionality."""
    print("🧪 Testing Anthropic Cost Estimation...")
    
    provider = AnthropicProvider()
    mock_kv_client = MockSecretClient()
    await provider.initialize(mock_kv_client)
    
    test_prompt = "Write a comprehensive analysis of renewable energy trends in 2025."
    
    for model in ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307", "claude-3-opus-20240229"]:
        cost = provider.estimate_cost(test_prompt, model, max_tokens=1000)
        print(f"✅ Estimated cost for {model}: ${cost:.6f}")
    
    return True


async def test_status_reporting():
    """Test provider status reporting."""
    print("\n🧪 Testing Anthropic Status Reporting...")
    
    provider = AnthropicProvider()
    mock_kv_client = MockSecretClient()
    await provider.initialize(mock_kv_client)
    
    status = provider.get_status()
    
    print("✅ Anthropic Provider Status:")
    print(f"   - Name: {status['name']}")
    print(f"   - Provider: {status['provider']}")
    print(f"   - Enabled: {status['enabled']}")
    print(f"   - Initialized: {status['initialized']}")
    print(f"   - Budget: ${status['current_usage']:.2f} / ${status['budget_limit']:.2f}")
    print(f"   - Available: {status['available']}")
    print(f"   - Models: {len(status['models'])}")
    print(f"   - Default model: {status['default_model']}")
    
    return True


async def test_model_recommendations():
    """Test model recommendation system."""
    print("\n🧪 Testing Anthropic Model Recommendations...")
    
    provider = AnthropicProvider()
    
    task_types = ["general", "code", "fast", "analysis", "creative", "cost_effective"]
    
    print("✅ Model Recommendations:")
    for task_type in task_types:
        recommended = provider.get_recommended_model(task_type)
        print(f"   - {task_type}: {recommended}")
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting Anthropic Provider Tests")
    print("=" * 50)
    
    tests = [
        test_anthropic_provider_initialization,
        test_model_info,
        test_cost_estimation,
        test_status_reporting,
        test_model_recommendations
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
        print("🎉 All tests passed! Anthropic integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
