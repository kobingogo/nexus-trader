import os
import json
import time
from openai import OpenAI

def test_model_streaming(model_name):
    api_key = "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"
    base_url = "https://integrate.api.nvidia.com/v1"
    
    print(f"\n--- Testing streaming with {model_name} ---")
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    start_time = time.time()
    received_content = False
    
    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Counting from 1 to 5, one number per line."}
            ],
            stream=True,
            timeout=20
        )
        
        for chunk in stream:
            if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                if not received_content:
                    print(f"Time to first token: {time.time() - start_time:.2f}s")
                    received_content = True
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        if not received_content:
            print("\nResult: Stream connected but NO content received (Likely HANG).")
        else:
            print("\nResult: SUCCESS.")
            
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    models = ["z-ai/glm4.7", "deepseek-ai/deepseek-v3.2"]
    for m in models:
        test_model_streaming(m)
