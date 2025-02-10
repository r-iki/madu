import requests

CLOUDFLARE_API_TOKEN = "WwojWCK5fI-4rnfCZp0QwKtn7YZ7xwRI0V63sZkY"
ZONE_ID = "0111fb3a5c2406ccf14ac15b2aedd594"
RECORD_NAME = "madu.software"
EMAIL = "mail@riki.my.id"


def get_public_ip():
    response = requests.get("https://api64.ipify.org?format=json")
    return response.json().get("ip")

def get_dns_record_id():
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?type=A&name={RECORD_NAME}"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    response = requests.get(url, headers=headers)
    records = response.json()
    if records["success"] and records["result"]:
        return records["result"][0]["id"]
    else:
        raise Exception("DNS record not found")

def update_dns_record(ip):
    record_id = get_dns_record_id()
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "A",
        "name": RECORD_NAME,
        "content": ip,
        "ttl": 120,
        "proxied": False
    }
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"IP Updated to {ip}")
    else:
        print(f"Failed to update DNS: {response.text}")

if __name__ == "__main__":
    current_ip = get_public_ip()
    update_dns_record(current_ip)