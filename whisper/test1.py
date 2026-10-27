import os
# Force disable proxy for local connections to avoid connection issues
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

from ollama import Client

# Initialize the client pointing to your local Ollama instance
client = Client(host='http://127.0.0.1:11434')

# Path to your local image file
image_path = "test.png"

try:
    response = client.chat(
        model='qwen25vl',  # Use the vision-enabled tag
        messages=[
            {
                'role': 'user',
                'content': '从头图片中提取文字，并按照对话的时间顺序排序，输出为json',
                'images': [image_path]  # Pass the absolute local path string
            }
        ]
    )
    print("--- Local Ollama Response ---")
    print(response.message.content)
    
    response = client.chat(
        model='qwen2.5',  # Use the vision-enabled tag
        messages=[
            {
                'role': 'user',
                'content': '根据以下对话，总结一下：'+response.message.content,
            }
        ]
    )    
    print(response.message)

except Exception as e:
    print(f"Error: {e}")