import os
import json
import tempfile
import subprocess
from openai import OpenAI


def get_prompt_from_user():
    """Opens a temporary file in the default editor for the user to enter a prompt."""
    editor = os.getenv("EDITOR", "vim")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as tf:
        tf.write("# Enter your prompt here\n")
        temp_filename = tf.name
    subprocess.call([editor, temp_filename])
    with open(temp_filename, "r") as f:
        prompt = f.read()
    os.remove(temp_filename)
    return prompt


def main():
    """Main function to test the service."""
    service_url = os.getenv("SERVICE_URL")
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("MODEL_NAME", "gpt-4")

    if not service_url:
        print("Error: SERVICE_URL environment variable not set.")
        return

    if not api_key:
        print("Error: API_KEY environment variable not set.")
        return

    try:
        with open("tools.json", "r") as f:
            tools = json.load(f)
    except FileNotFoundError:
        print("Error: tools.json not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode tools.json.")
        return

    client = OpenAI(
        base_url=service_url,
        api_key=api_key,
    )

    prompt = get_prompt_from_user()

    if not prompt.strip():
        print("Prompt is empty. Exiting.")
        return

    messages = [{"role": "user", "content": prompt}]

    print("Sending request to the service...")

    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=True,
    )

    tool_calls = []
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
        if delta.tool_calls:
            for tool_call_chunk in delta.tool_calls:
                if len(tool_calls) <= tool_call_chunk.index:
                    tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})

                tc = tool_calls[tool_call_chunk.index]
                if tool_call_chunk.id:
                    tc["id"] += tool_call_chunk.id
                if tool_call_chunk.function.name:
                    tc["function"]["name"] += tool_call_chunk.function.name
                if tool_call_chunk.function.arguments:
                    tc["function"]["arguments"] += tool_call_chunk.function.arguments

    if tool_calls:
        print("\n\nTool calls:")
        for tc in tool_calls:
            print(json.dumps(tc, indent=2))

    print()


if __name__ == "__main__":
    main()
