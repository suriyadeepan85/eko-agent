import boto3, json

client = boto3.client("bedrock-runtime", region_name="us-east-1")

response = client.converse(
    modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    messages=[{"role": "user", "content": [{"text": "what is difference between aws and azure."}]}],
    inferenceConfig={"maxTokens": 50},
)

print(response["output"]["message"]["content"][0]["text"])
print("tokens:", response["usage"])