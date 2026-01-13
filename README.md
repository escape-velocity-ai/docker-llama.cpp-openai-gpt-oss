# docker-llama.cpp-openai-gpt-oss
A general docker container for running openai gpt oss models using llama.cpp

## Running on GCP Cloud Run

For detailed instructions on how to deploy this service on Google Cloud Run, see the [GCP Cloud Run documentation](RUN-ON-GCP.md).

## Testing the service

This repository includes a python script to test that the service is running correctly. The script will send requests to the service and print the response.

### Prerequisites

- Python 3.6+
- `pip` for installing dependencies

### Setup

1.  Install the required python packages:

    ```bash
    pip install -r requirements.txt
    ```

2.  Set the following environment variables:

    ```bash
    export SERVICE_URL="<your_service_url>"
    export API_KEY="<your_api_key>"
    export MODEL_NAME="<your_model_name>" # Optional, defaults to gpt-4
    ```

### Usage

Run the script:

```bash
python scripts/test_service.py
```

The script will open a temporary file in your default editor for you to enter a prompt. Once you save and close the file, the script will send the prompt to the service and print the response.
