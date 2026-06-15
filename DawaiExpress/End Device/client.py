import requests

def makeRequest(ip, port, route, json):
    url = f"http://{ip}:{port}{route}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=json, headers=headers, timeout=5)
        print("Status Code:", response.status_code)
        print("Response:", response.json())
        print("Extracted Response:", response.json()["status"])
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)

if __name__ == "__main__":
    makeRequest("192.168.0.32", 8081, "/alerts", {"alert": "medicines not taken"})