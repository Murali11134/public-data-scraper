import requests
import json
import re

def call_llm(prompt):
    url = "http://localhost:11434/api/generate"

    data = {
        "model": "llama3:instruct",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=data, timeout=180)
        res_json = response.json()

        text = res_json.get("response", "")
        print("RAW:", text)

        # 🔥 STEP 1: Try direct parse
        try:
            return json.loads(text)
        except:
            pass

        # 🔥 STEP 2: Try unescaping string
        try:
            cleaned = text.strip().encode().decode("unicode_escape")
            return json.loads(cleaned)
        except:
            pass

        # 🔥 STEP 3: Extract JSON manually
        match = re.search(r"\{.*\}", text)
        if match:
            json_text = match.group()
            json_text = json_text.encode().decode("unicode_escape")
            return json.loads(json_text)

        return {
            "error": "No JSON found",
            "raw_response": text
        }

    except Exception as e:
        return {
            "error": "LLM call failed",
            "details": str(e)
        }