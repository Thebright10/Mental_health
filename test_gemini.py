from google import genai
client=genai.Client(api_key="AIzaSyD6MhTWUEVQ-dZBojvBqPCcidw5IuJ-16U")
models=client.models.list()
for m in models:
    print(m.name)