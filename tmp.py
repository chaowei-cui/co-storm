import os
from openai import OpenAI

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
    api_key="a14c64be-5225-478d-b6d4-d54912ad77ea",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

print("----- embeddings request -----")
resp = client.embeddings.create(
    model="ep-20250228235419-n5vjc",
    input=["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
    encoding_format="float"
)
print(resp)