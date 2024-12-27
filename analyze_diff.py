import os
import subprocess
import requests
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Environment variables from Bitbucket
BITBUCKET_PR_DESTINATION_BRANCH = os.getenv("BITBUCKET_PR_DESTINATION_BRANCH")
BITBUCKET_BRANCH = os.getenv("BITBUCKET_BRANCH")
BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE")
BITBUCKET_REPO_SLUG = os.getenv("BITBUCKET_REPO_SLUG")
BITBUCKET_PR_ID = os.getenv("BITBUCKET_PR_ID")
BITBUCKET_USER = os.getenv("BITBUCKET_USER")
BITBUCKET_APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_API_URL = "https://aiop-test.item.com/v1/chat-messages"

def run_command(command):
    logging.info(f"Running command: {command}")
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error(f"Command failed: {result.stderr}")
        exit(1)
    return result.stdout

def fetch_diff():
    logging.info("Fetching full repository...")
    run_command("git fetch --all")

    logging.info("Fetching target branch...")
    run_command(f"git fetch origin {BITBUCKET_PR_DESTINATION_BRANCH}")

    logging.info("Generating code diff...")
    diff = run_command(f"git diff --unified=0 origin/{BITBUCKET_PR_DESTINATION_BRANCH}..origin/{BITBUCKET_BRANCH}")
    
    if not diff.strip():
        logging.warning("No code changes detected.")
        exit(1)
    
    return diff

def send_to_dify(diff):
    logging.info("Sending code diff to Dify...")
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {"code_diff": diff},
        "query": "Please analyze this code diff.",
        "response_mode": "streaming"
    }
    
    response = requests.post(DIFY_API_URL, headers=headers, json=payload)
    if response.status_code == 401:
        logging.error("Authorization failed. Please check the DIFY_API_KEY.")
        exit(1)
    
    response_data = response.text
    logging.info("Received response from Dify.")
    return response_data

def post_comment_to_pr(feedback):
    logging.info("Adding Dify feedback to Pull Request...")
    pr_comment_url = f"https://api.bitbucket.org/2.0/repositories/{BITBUCKET_WORKSPACE}/{BITBUCKET_REPO_SLUG}/pullrequests/{BITBUCKET_PR_ID}/comments"
    auth = (BITBUCKET_USER, BITBUCKET_APP_PASSWORD)
    payload = {"content": {"raw": f"Dify Feedback: {feedback}"}}
    
    response = requests.post(pr_comment_url, auth=auth, json=payload)
    if response.status_code != 201:
        logging.error(f"Failed to post comment: {response.status_code}, {response.text}")
        exit(1)
    
    logging.info("Feedback posted successfully.")

if __name__ == "__main__":
    try:
        diff = fetch_diff()
        feedback = send_to_dify(diff)
        post_comment_to_pr(feedback)
    except Exception as e:
        logging.exception("An error occurred during script execution.")
        exit(1)
