import httpx
from ollama import chat
from ollama import ChatResponse

url = "http://147.96.81.252:8000/info"
response_api = httpx.get(url)

response: ChatResponse = chat(model='qwen3-vl:8b', messages=[
  {
    'role': 'user',
    'content': response_api.text,
  },
])
print(response['message']['content'])

