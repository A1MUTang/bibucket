import os
import sys
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main(diff_file):
    try:
        # Read the code diff from the file
        logging.info("Reading the code diff from file: %s", diff_file)
        with open(diff_file, "r") as file:
            code_diff = file.read()
        logging.info("Successfully read the code diff.")

        # Define the Dify API URL and headers
        url = "https://aiop-test.item.com/v1/chat-messages"
        headers = {
            "Authorization": "Bearer app-npWE2itifhPtymIPOwWmHYRM",
            "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # Prepare the payload
        data = {
            "inputs": {"code_diff": code_diff},
            "query": "Analyze this code diff and provide feedback.",
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "abc-123",
            "files": [
                {
                    "type": "image",
                    "transfer_method": "remote_url",
                    "url": "https://cloud.dify.ai/logo/logo-site.png",
                }
            ],
        }

        logging.info("Sending request to Dify...")
        response = requests.post(url, headers=headers, json=data)

        # Log the response from Dify
        logging.info("Response received from Dify:")
        logging.info(response.text)

        # Check for authorization failure
        if "unauthorized" in response.text:
            logging.error("Authorization failed. Please check the DIFY_API_KEY.")
            sys.exit(1)

        # Prepare to add feedback to the PR
        bitbucket_url = f"https://api.bitbucket.org/2.0/repositories/{os.getenv('BITBUCKET_WORKSPACE')}/{os.getenv('BITBUCKET_REPO_SLUG')}/pullrequests/{os.getenv('BITBUCKET_PR_ID')}/comments"
        bitbucket_auth = (os.getenv('BITBUCKET_USER'), os.getenv('BITBUCKET_APP_PASSWORD'))
        bitbucket_headers = {"Content-Type": "application/json"}
        bitbucket_payload = {
            "content": {
                "raw": f"Dify Feedback: {response.text}"
            }
        }

        logging.info("Adding feedback to Bitbucket PR...")
        bitbucket_response = requests.post(bitbucket_url, auth=bitbucket_auth, headers=bitbucket_headers, json=bitbucket_payload)

        # Log the Bitbucket API response
        logging.info("Response received from Bitbucket:")
        logging.info(bitbucket_response.text)

    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python analyze_diff.py <diff_file>")
        sys.exit(1)
    
    main(sys.argv[1])
