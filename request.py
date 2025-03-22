import requests
import base64
import dotenv
dotenv.load_dotenv()
import os

AUTH_TOKEN = "Hnp5N4ve_Oc3WIrCpRb9oHAAJt7FglM1oEOtlWG1J1M_TVQzZ5QwriBtc82qI-vbGDT1PPouk7P5-IcP41HaFw=="

def transcribe(file_path, wd=True):

    with open(file_path, "rb") as file:
        FILE = base64.b64encode(file.read()).decode("utf-8")

    payload = {
        "file": FILE,
        "with_diarization": True
    }

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(os.environ['BEAM_ENDPOINT'], headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        return {'segments': [],
                'status':'error'}

async def check(task_id):
    url = f"https://api.beam.cloud/v2/task/{task_id}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(e)
        return {}
