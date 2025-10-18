import requests


def fetch_latest_headlines():
    # Example: CryptoPanic public API (no key required for headlines)
    url = "https://cryptopanic.com/api/v1/posts/?public=true&currencies=BTC,ETH"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Return a list of headlines
        return [item["title"] for item in data.get("results", [])]
    except Exception as e:
        print(f"[VictoryBot][NEWS][ERROR] {e}")
        return []
