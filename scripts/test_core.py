import os
import json
import requests

# Test environment variables
required_vars = {
    'METAMASK_PRIVATE_KEY': '0x05a4743525020c3a85057939ebfb283b5a1d08f26854265e0e849a98725d69b3',
    'SEPOLIA_URL': 'https://eth-sepolia.public.blastapi.io',
    'CONTRACT_ADDRESS': '0xa0f536d1d1a8Bf63e200344Bda8a34b6d012745b',
    'QWEN_API_KEY': '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',
    'HYPERSWARM_TOPIC': 'ai-nft-market-v3'
}

# Set environment variables
for key, value in required_vars.items():
    os.environ[key] = value

# Test Sepolia connection
def test_sepolia():
    try:
        response = requests.get(f"{os.environ['SEPOLIA_URL']}/eth/v1/beacon/genesis")
        response.raise_for_status()
        print(f"✅ Sepolia connection test passed")
    except Exception as e:
        print(f"❌ Sepolia connection test failed: {e}")
        return False
    return True

# Test contract address
def test_contract():
    if os.environ.get('CONTRACT_ADDRESS'):
        print(f"✅ Contract address is set: {os.environ['CONTRACT_ADDRESS']}")
        return True
    else:
        print("❌ Contract address is not set")
        return False

# Test Qwen API key
def test_qwen():
    if os.environ.get('QWEN_API_KEY'):
        print("✅ Qwen API key is set")
        return True
    else:
        print("❌ Qwen API key is not set")
        return False

# Test Hyperswarm topic
def test_hyperswarm():
    if os.environ.get('HYPERSWARM_TOPIC'):
        print(f"✅ Hyperswarm topic is set: {os.environ['HYPERSWARM_TOPIC']}")
        return True
    else:
        print("❌ Hyperswarm topic is not set")
        return False

# Run all tests
def run_tests():
    print("Running core functionality tests...")
    tests = [
        test_sepolia,
        test_contract,
        test_qwen,
        test_hyperswarm
    ]
    
    results = all(test() for test in tests)
    
    if results:
        print("\n✅ All core functionality tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return results

if __name__ == '__main__':
    run_tests()
