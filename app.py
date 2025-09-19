from flask import Flask, request, jsonify, render_template_string
import random
import string
import requests
import logging
import re
import subprocess
import os
import shutil
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

stored_keys = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>QuackExecutor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37); backdrop-filter: blur(4px); width: 100%; max-width: 500px; text-align: center; animation: fadeIn 0.5s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        h1 { color: #2c3e50; margin-bottom: 1.5rem; font-size: 2.2rem; text-transform: uppercase; letter-spacing: 2px; }
        .key-label { color: #34495e; font-size: 1.1rem; margin-bottom: 0.5rem; }
        .textbox { width: 100%; padding: 0.8rem; font-size: 1rem; border: 2px solid #3498db; border-radius: 8px; margin-bottom: 1rem; background: #f8f9fa; color: #2c3e50; transition: all 0.3s ease; }
        .textbox:focus { outline: none; border-color: #2980b9; box-shadow: 0 0 8px rgba(52, 152, 219, 0.3); }
        .btn { padding: 0.8rem 2rem; font-size: 1rem; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; text-transform: uppercase; font-weight: bold; }
        .btn:hover { background: #2980b9; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }
        .message { margin-top: 1.5rem; color: #e74c3c; font-size: 1.1rem; font-weight: 500; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        .noodle-emoji { font-size: 1.5rem; margin-left: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>QuackExecutor</h1>
        <p class="key-label">Your Key:</p>
        <input type="text" class="textbox" value="{{ key }}" readonly>
        <button class="btn" onclick="navigator.clipboard.writeText('{{ key }}').then(() => alert('Key copied to clipboard!'))">Copy</button>
        <p class="message">Thank you for getting your key, added 9/50 bowl of noodles! <span class="noodle-emoji">🍜💖</span></p>
    </div>
</body>
</html>
"""

def generate_random_key():
    key = f"Quack_{''.join(random.choices(string.digits, k=16))}"
    logger.info(f"Generated new key: {key}")
    return key

def setup_cloudflared():
    cloudflared_path = os.path.join(os.getcwd(), 'cloudflared')
    if os.path.exists(cloudflared_path) and os.access(cloudflared_path, os.X_OK):
        logger.info("cloudflared binary already exists and is executable")
        return
    if not shutil.which('curl'):
        logger.error("curl not found. Install it with: apt-get install curl")
        raise RuntimeError("Missing curl")
    logger.info("Installing cloudflared binary...")
    try:
        subprocess.run(['curl', '-L', 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64', '-o', 'cloudflared'], check=True)
        subprocess.run(['chmod', '+x', 'cloudflared'], check=True)
        subprocess.run(['./cloudflared', 'tunnel', '--version'], check=True)
        logger.info("cloudflared binary installed and verified successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install or verify cloudflared: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error installing cloudflared: {str(e)}")
        raise

def start_cloudflared_tunnel():
    cloudflared_path = os.path.join(os.getcwd(), 'cloudflared')
    if not os.path.exists(cloudflared_path) or not os.access(cloudflared_path, os.X_OK):
        logger.error("cloudflared binary not found or not executable")
        raise RuntimeError("cloudflared not installed")
    logger.info("Setting up Cloudflare tunnel...")
    try:
        subprocess.run([cloudflared_path, 'tunnel', 'route', 'dns', 'flaskkey', 'key.ducknovis.site'], check=True)
        subprocess.Popen([cloudflared_path, 'tunnel', '--config', os.path.expanduser('~/.cloudflared/config.yml'), 'run', 'flaskkey'])
        logger.info("Cloudflare tunnel started")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set up Cloudflare tunnel: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error setting up Cloudflare tunnel: {str(e)}")
        raise

@app.route('/key', methods=['GET'])
def show_key():
    key = request.args.get('key', '')
    logger.info(f"Accessing /key endpoint with key: {key} from IP: {request.remote_addr}, Headers: {dict(request.headers)}")
    return render_template_string(HTML_TEMPLATE, key=key)

@app.route('/createkey', methods=['POST'])
def create_key():
    logger.info(f"Received /createkey POST request from IP: {request.remote_addr}, Headers: {dict(request.headers)}")
    random_key = generate_random_key()
    api_params = {
        'api': '67cd970310c4b82d8433cf9c',
        'url': f'https://key.ducknovis.site/key?key={random_key}'  # Fixed query parameter to ?key=
    }
    logger.info(f"Sending request to link4m API with params: {api_params}")
    try:
        response = requests.get('https://link4m.co/api-shorten/v2', params=api_params, timeout=10)
        logger.info(f"Received raw response from link4m API: Status={response.status_code}, Content={response.text}")
        if not response.text:
            logger.error("link4m API returned empty response")
            return jsonify({'status': 'error', 'message': 'Link shortening service returned empty response'}), 500
        try:
            response_data = response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON response from link4m API: {str(e)}, Raw Content: {response.text}")
            return jsonify({'status': 'error', 'message': f'Invalid response from link shortening service: {response.text}'}), 500
        if response.status_code == 200 and response_data.get('status') == 'success' and 'shortenedUrl' in response_data:
            stored_keys[random_key] = True
            logger.info(f"Stored key: {random_key}")
            response_payload = {
                'status': 'success',
                'link': response_data['shortenedUrl'],
                'key': random_key
            }
            logger.info(f"Returning response: {response_payload}")
            return jsonify(response_payload), 200
        else:
            error_message = response_data.get('message', 'Failed to create shortened URL')
            logger.error(f"link4m API returned error: Status={response.status_code}, Content={response_data}")
            return jsonify({'status': 'error', 'message': error_message}), 500
    except requests.exceptions.Timeout:
        logger.error("Timeout calling link4m API")
        return jsonify({'status': 'error', 'message': 'Link shortening service timed out'}), 500
    except requests.exceptions.ConnectionError:
        logger.error("Connection error calling link4m API")
        return jsonify({'status': 'error', 'message': 'Failed to connect to link shortening service'}), 500
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling link4m API: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Network error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /createkey: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Unexpected error: {str(e)}'}), 500

@app.route('/submitkey', methods=['POST'])
def submit_key():
    logger.info(f"Received /submitkey request from IP: {request.remote_addr}, Headers: {dict(request.headers)}")
    try:
        data = request.get_json()
        logger.info(f"Received JSON payload: {data}")
        key = data.get('key') if data else None
        if not key:
            logger.warning("No key provided in /submitkey request")
            return jsonify({'status': 'error', 'message': 'No key provided'}), 400
        if not re.match(r'^Quack_\d{16}$', key):
            logger.warning(f"Invalid key format: {key}")
            response_payload = {'status': 'success', 'isValid': False}
            logger.info(f"Returning response: {response_payload}")
            return jsonify(response_payload), 200
        logger.info(f"Checking key: {key}")
        if key in stored_keys:
            del stored_keys[key]
            logger.info(f"Valid key submitted: {key}, removed from storage")
            response_payload = {'status': 'success', 'isValid': True}
            logger.info(f"Returning response: {response_payload}")
            return jsonify(response_payload), 200
        else:
            logger.info(f"Invalid key submitted: {key}")
            response_payload = {'status': 'success', 'isValid': False}
            logger.info(f"Returning response: {response_payload}")
            return jsonify(response_payload), 200
    except ValueError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Invalid JSON payload'}), 400
    except Exception as e:
        logger.error(f"Error processing /submitkey request: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    try:
        setup_cloudflared()
        start_cloudflared_tunnel()
    except Exception as e:
        logger.error(f"Failed to set up cloudflared, continuing with local server: {str(e)}")
    app.run(host='0.0.0.0', port=26570)
