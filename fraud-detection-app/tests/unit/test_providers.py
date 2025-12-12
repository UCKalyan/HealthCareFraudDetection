import urllib.request
import urllib.parse
import json

def test_providers_endpoint():
    print("--- Testing /providers Endpoint ---")
    try:
        params = {
            "page": 1, 
            "limit": 10,
            "npi_filter": "",
            "name_filter": "",
            "specialty_filter": "",
            "sort_by": "npi",
            "order": "asc"
        }
        query_string = urllib.parse.urlencode(params)
        url = f"http://127.0.0.1:8000/providers?{query_string}"
        
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"✅ Status Code: 200")
                print(f"Total Records: {data.get('total')}")
                print(f"Data Length: {len(data.get('data', []))}")
                if data.get('data'):
                    print(f"Sample Provider: {json.dumps(data['data'][0], indent=2)}")
            else:
                print(f"❌ Status Code: {response.status}")
                print(response.read().decode())
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_providers_endpoint()
