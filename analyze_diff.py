import logging
import os
import subprocess
import requests

# 配置日志记录
def setup_logging():
    """设置日志格式和输出到控制台"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 设置最低日志级别

    console_handler = logging.StreamHandler()  # 创建控制台处理器
    console_handler.setLevel(logging.DEBUG)

    # 定义日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(console_handler)

setup_logging()

def run_command(command):
    """运行 shell 命令并记录输出和错误"""
    try:
        logging.info(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        logging.debug(f"Command output: {result.stdout.strip()}")
        if result.stderr.strip():
            logging.error(f"Command error: {result.stderr.strip()}")
        return result
    except Exception as e:
        logging.error(f"Failed to run command {command}: {e}")
        raise

def fetch_environment_variables():
    """记录环境变量"""
    logging.info("Fetching environment variables...")
    env_vars = {key: os.environ.get(key) for key in ['GIT_TOKEN', 'GIT_URL', 'DIFFY_API_URL', 'DIFFY_API_TOKEN']}
    logging.debug(f"Environment variables: {env_vars}")
    return env_vars

def send_request_to_dify(api_url, diff, headers):
    """发送 diff 到 Dify 并记录请求/响应"""
    try:
        logging.info("Sending code diff to Dify...")
        response = requests.post(api_url, json=diff, headers=headers)
        logging.debug(f"Dify Response Status Code: {response.status_code}")
        logging.debug(f"Dify Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to send request to Dify: {e}")
        raise

def main():
    # 记录运行环境
    env_vars = fetch_environment_variables()

    # 拉取代码库和目标分支
    run_command("git fetch --all")
    run_command("git fetch origin dev")

    # 生成代码 diff
    diff_command = "git diff --unified=0 origin/dev..origin/feature/addUnisBaseCharge"
    diff_result = run_command(diff_command)
    diff = diff_result.stdout

    # 构造 Dify 请求
    api_url = env_vars['DIFFY_API_URL']
    headers = {'Authorization': f"Bearer {env_vars['DIFFY_API_TOKEN']}"}
    response = send_request_to_dify(api_url, {'diff': diff}, headers)

    # 添加反馈到 Pull Request
    try:
        logging.info("Adding Dify feedback to Pull Request...")
        pr_response = requests.post(
            f"{env_vars['GIT_URL']}/comments",
            json={"body": response.get("feedback")},
            headers={"Authorization": f"token {env_vars['GIT_TOKEN']}"}
        )
        pr_response.raise_for_status()
        logging.info("Feedback successfully added to Pull Request.")
    except requests.RequestException as e:
        logging.error(f"Failed to post comment: {e}")

if __name__ == "__main__":
    main()
