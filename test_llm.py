import json
from urllib import request, error

def test_gemini():
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    api_key = "AIzaSyBakAn5zaMy9Nwl0SRwMthNz5mF4_FfmAw"
    
    final_url = f"{api_url}?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": "Hello, are you working?"}]}]
    }
    
    print(f"Testing URL: {api_url}")
    
    try:
        req = request.Request(
            final_url, 
            method="POST", 
            headers={"Content-Type": "application/json"}, 
            data=json.dumps(payload).encode("utf-8")
        )
        with request.urlopen(req) as response:
            print(f"Status Code: {response.status}")
            print(f"Response: {response.read().decode()}")
    except error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(f"Error Body: {e.read().decode()}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    test_gemini()
