#!/usr/bin/env python3
"""
Quick diagnostic script to check OpenAI Responses API availability
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("OpenAI Responses API Diagnostic")
print("=" * 60)

# Check OpenAI package
try:
    import openai
    print(f"✅ OpenAI package installed: version {openai.__version__}")
except ImportError as e:
    print(f"❌ OpenAI package not installed: {e}")
    sys.exit(1)

# Check if AsyncOpenAI exists
try:
    from openai import AsyncOpenAI
    print("✅ AsyncOpenAI class available")
except ImportError as e:
    print(f"❌ AsyncOpenAI not available: {e}")
    print("📦 Please upgrade: pip install --upgrade openai")
    sys.exit(1)

# Check API key
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ OPENAI_API_KEY found (length: {len(api_key)})")
else:
    print("❌ OPENAI_API_KEY not set in environment")
    sys.exit(1)

# Initialize client
try:
    client = AsyncOpenAI(api_key=api_key)
    print("✅ AsyncOpenAI client initialized")
except Exception as e:
    print(f"❌ Failed to initialize AsyncOpenAI: {e}")
    sys.exit(1)

# Check for responses attribute
if hasattr(client, 'responses'):
    print("✅ client.responses attribute exists")
    print(f"   Type: {type(client.responses)}")
    
    # Check for create method
    if hasattr(client.responses, 'create'):
        print("✅ client.responses.create() method exists")
    else:
        print("❌ client.responses.create() method not found")
else:
    print("❌ client.responses attribute NOT found")
    print("\n📦 Your OpenAI SDK version does not support the Responses API")
    print("   Current version:", openai.__version__)
    print("   Required version: >= 1.50.0 (estimated)")
    print("\n   To upgrade:")
    print("   pip install --upgrade openai")
    sys.exit(1)

# Check what's available on the client
print("\n📋 Available attributes on AsyncOpenAI client:")
attrs = [attr for attr in dir(client) if not attr.startswith('_')]
for attr in sorted(attrs):
    print(f"   - {attr}")

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED - Responses API is available!")
print("=" * 60)
print("\n🚀 You can use streaming responses with the Responses API")


