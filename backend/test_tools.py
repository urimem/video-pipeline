import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()
KIE_API_KEY = os.getenv("KIE_API_KEY", "")
KIE_URL = "https://api.kie.ai/gemini-2.5-flash/v1/chat/completions"

# Define the function the model can call
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    # In a real application, this would call an external weather API
    if location == "Boston":
        return json.dumps({"location": "Boston", "temperature": "72", "unit": "fahrenheit"})
    elif location == "San Francisco":
        return json.dumps({"location": "San Francisco", "temperature": "65", "unit": "fahrenheit"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def run_conversation():
    # --- Step 1: Send the user prompt and function definition to the model ---
    messages = [{"role": "user", "content": "What's the weather in San Francisco?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    # API request to kie.ai chat completions endpoint
    # Note: Replace with the actual kie.ai chat endpoint if different from OpenAI spec
    response = requests.post(
        KIE_URL,
        headers={"Authorization": f"Bearer {KIE_API_KEY}"},
        json={
            "messages": messages,
            "tools": tools,
        }
    )
    print("Status:", response.status_code)
    print("Raw response:", response.text[:2000])
    response = response.json()

    # --- Step 2: Check if the model wants to call a function ---
    message = response["choices"][0]["message"]
    if message.get("tool_calls"):
        # --- Step 3: Extract function details and call the function ---
        first_tool_call = message["tool_calls"][0]
        function_name = first_tool_call["function"]["name"]
        function_args = json.loads(first_tool_call["function"]["arguments"])

        if function_name == "get_current_weather":
            function_response = get_current_weather(
                location=function_args.get("location"),
                unit=function_args.get("unit")
            )
            
            # --- Step 4: Append the function result to messages and make new API call ---
            messages.append(message) # Add the assistant's function call message
            messages.append(
                {
                    "tool_call_id": first_tool_call["id"],
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
            
            # Second API request with the function output appended
            second_response = requests.post(
                KIE_URL,
                headers={"Authorization": f"Bearer {KIE_API_KEY}"},
                json={"messages": messages},
            ).json()

            return second_response["choices"][0]["message"]["content"]

    return message["content"]

# Example usage:
weather_info = run_conversation()
print(weather_info)
