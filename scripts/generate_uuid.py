
import uuid

def generate_api_key():
    """
    Generates a new UUID and prints it to the console.
    """
    api_key = uuid.uuid4()
    print(api_key)

if __name__ == "__main__":
    generate_api_key()
