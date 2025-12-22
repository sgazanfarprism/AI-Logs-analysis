"""
Quick test script for Gemini API integration
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import load_yaml_config
from utils.logger import get_logger

logger = get_logger(__name__)


def test_gemini_connection():
    """Test Gemini API connection"""
    
    print("=" * 60)
    print("GEMINI API CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Load config
        print("\n1. Loading AI configuration...")
        config = load_yaml_config("config/ai.yaml")
        print(f"   ✓ Provider: {config['provider']}")
        print(f"   ✓ Model: {config['model']}")
        
        # Initialize Gemini
        print("\n2. Initializing Gemini client...")
        import google.generativeai as genai
        genai.configure(api_key=config["api_key"])
        print("   ✓ Gemini client configured")
        
        # Create model
        print("\n3. Creating GenerativeModel...")
        model = genai.GenerativeModel(config["model"])
        print(f"   ✓ Model created: {config['model']}")
        
        # Test simple generation
        print("\n4. Testing content generation...")
        test_prompt = "Say 'Hello from Gemini!' and confirm you are working."
        response = model.generate_content(test_prompt)
        print(f"   ✓ Response received: {response.text[:100]}...")
        
        # Test structured generation
        print("\n5. Testing structured JSON generation...")
        json_prompt = """
        Generate a JSON response with this structure:
        {
            "status": "success",
            "message": "Gemini API is working",
            "capabilities": ["text generation", "analysis", "reasoning"]
        }
        """
        response = model.generate_content(json_prompt)
        print(f"   ✓ JSON Response: {response.text[:200]}...")
        
        print("\n" + "=" * 60)
        print("✅ GEMINI API TEST PASSED")
        print("=" * 60)
        print("\nYour Gemini API is configured correctly and ready to use!")
        print("You can now run the full analysis system.")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ GEMINI API TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Check your GEMINI_API_KEY in .env file")
        print("2. Verify the API key is valid at: https://makersuite.google.com/app/apikey")
        print("3. Ensure google-generativeai package is installed: pip install google-generativeai")
        
        return False


if __name__ == "__main__":
    success = test_gemini_connection()
    sys.exit(0 if success else 1)
