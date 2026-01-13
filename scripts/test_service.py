import os
import json
import tempfile
import subprocess
import requests


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

    prompt = get_prompt_from_user()

    if not prompt.strip():
        print("Prompt is empty. Exiting.")
        return

    messages = [{"role": "user", "content": prompt}]

    print("Sending request to the service...")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = {
        "model": model_name,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "stream": True,
    }

    try:
        response = requests.post(
            f"{service_url}/completion",
            headers=headers,
            json=data,
            stream=True,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return

    tool_calls = []
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8")
        if not line.startswith("data: "):
            continue

        json_str = line[len("data: "):]
        if json_str == "[DONE]":
            break

        try:
            chunk = json.loads(json_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content")
            if content:
                print(content, end="", flush=True)

            if "tool_calls" in delta and delta["tool_calls"]:
                for tool_call_chunk in delta["tool_calls"]:
                    index = tool_call_chunk["index"]
                    if len(tool_calls) <= index:
                        tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})

                    tc = tool_calls[index]
                    if "id" in tool_call_chunk and tool_call_chunk["id"]:
                        tc["id"] += tool_call_chunk["id"]
                    if "function" in tool_call_chunk:
                        if "name" in tool_call_chunk["function"] and tool_call_chunk["function"]["name"]:
                            tc["function"]["name"] += tool_call_chunk["function"]["name"]
                        if "arguments" in tool_call_chunk["function"] and tool_call_chunk["function"]["arguments"]:
                            tc["function"]["arguments"] += tool_call_chunk["function"]["arguments"]
        except json.JSONDecodeError:
            print(f"\nError decoding JSON: {json_str}")
            continue

    if tool_calls:
        print("\n\nTool calls:")
        for tc in tool_calls:
            print(json.dumps(tc, indent=2))

    print()


if __name__ == "__main__":
    main()
