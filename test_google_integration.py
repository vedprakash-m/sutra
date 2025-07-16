#!/usr/bin/env python3

"""
Simple test script to validate Google AI integration.
This script tests the new Google provider without requiring pytest.
"""

import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared.llm_providers.google_provider import GoogleProvider
from api.shared.llm_providers.base_provider import TokenUsage, LLMResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSecretClient:
    """Mock Secret Client for testing without Azure Key Vault."""

    def __init__(self):
        self.secrets = {
            "google-api-key": type('Secret', (), {"value": "test-api-key"})(),
            "google-config": type('Secret', (), {"value": '{"budget_limit": 100.0, "priority": 1, "enabled": true, "default_model": "gemini-1.5-flash"}'})()
        }

    def get_secret(self, secret_name: str):
        if secret_name in self.secrets:
            return self.secrets[secret_name]
        raise Exception(f"Secret {secret_name} not found")


async def test_google_provider_initialization():
    """Test Google provider initialization."""
    print("🧪 Testing Google AI Provider Initialization...")

    provider = GoogleProvider()
    mock_kv_client = MockSecretClient()

    # Test initialization
    result = await provider.initialize(mock_kv_client)

    if result:
        print("✅ Google AI provider initialized successfully")
        print(f"   - Provider name: {provider.provider_name}")
        print(f"   - Default model: {provider.default_model}")
        print(f"   - Available models: {len(provider.get_models())}")
        print(f"   - Budget limit: ${provider.budget_limit}")
        return True
    else:
        print("❌ Failed to initialize Google AI provider")
        return False


async def test_model_info():
    """Test model information retrieval."""
    print("\n🧪 Testing Google AI Model Information...")

    provider = GoogleProvider()
    models = provider._get_available_models()

    print(f"✅ Found {len(models)} Google AI models:")
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
    print("🧪 Testing Google AI Cost Estimation...")

    provider = GoogleProvider()
    mock_kv_client = MockSecretClient()
    await provider.initialize(mock_kv_client)

    test_prompt = "Explain the latest developments in quantum computing and their potential impact on cryptography."

    for model in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]:
        cost = provider.estimate_cost(test_prompt, model, max_tokens=1500)
        print(f"✅ Estimated cost for {model}: ${cost:.6f}")

    return True


async def test_status_reporting():
    """Test provider status reporting."""
    print("\n🧪 Testing Google AI Status Reporting...")

    provider = GoogleProvider()
    mock_kv_client = MockSecretClient()
    await provider.initialize(mock_kv_client)

    status = provider.get_status()

    print("✅ Google AI Provider Status:")
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
    print("\n🧪 Testing Google AI Model Recommendations...")

    provider = GoogleProvider()

    task_types = ["general", "code", "fast", "analysis", "creative", "cost_effective"]

    print("✅ Model Recommendations:")
    for task_type in task_types:
        recommended = provider.get_recommended_model(task_type)
        print(f"   - {task_type}: {recommended}")

    return True


async def test_multimodal_capabilities():
    """Test multimodal capabilities detection."""
    print("\n🧪 Testing Google AI Multimodal Capabilities...")

    provider = GoogleProvider()
    models = provider._get_available_models()

    print("✅ Multimodal Capabilities:")
    for name, model_info in models.items():
        has_image_analysis = any(cap.value == "image_analysis" for cap in model_info.capabilities)
        print(f"   - {model_info.display_name}: {'🖼️  Image Analysis' if has_image_analysis else '📝 Text Only'}")

    return True


async def main():
    """Run all tests."""
    print("🚀 Starting Google AI Provider Tests")
    print("=" * 50)

    tests = [
        test_google_provider_initialization,
        test_model_info,
        test_cost_estimation,
        test_status_reporting,
        test_model_recommendations,
        test_multimodal_capabilities
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
        print("🎉 All tests passed! Google AI integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
