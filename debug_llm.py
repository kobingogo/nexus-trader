import os
import json
from openai import OpenAI

# Mock LLMProviderManager logic for simplicity
def test_streaming():
    api_key = "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"
    base_url = "https://integrate.api.nvidia.com/v1"
    model_name = "meta/llama-3.1-405b-instruct"
    
    print(f"Testing streaming with {model_name}...")
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Counting from 1 to 20, one number per line."}
            ],
            stream=True,
            timeout=30
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print("\nStream finished.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_streaming()
