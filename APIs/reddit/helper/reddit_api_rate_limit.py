import requests
import time
from requests.auth import HTTPBasicAuth

# Deine Zugangsdaten hier einfügen
client_id = 'u9wPL-7SY7LwVNTrImjS-w'
client_secret = '3Y-1RHbp2rizAZRRji79OdIdImQx5w'
username = 'FinBot_BA'
password = 'FOM-Dual-2021'

# Token abrufen
auth = HTTPBasicAuth(client_id, client_secret)
data = {'grant_type': 'password', 'username': username, 'password': password}
headers = {'User-Agent': 'RateLimitCheck/0.1'}

response = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
token = response.json().get('access_token')
if not token:
    print("Fehler beim Abrufen des Tokens.")
    exit()

# Setzt den Authentifizierungs-Header mit dem Token
headers['Authorization'] = f'bearer {token}'

# Beispielanfrage an die Reddit API (z.B. auf die Frontpage)
response = requests.get('https://oauth.reddit.com/', headers=headers)

# Auswertung der Rate-Limit-Header
rate_limit_used = response.headers.get('X-Ratelimit-Used')
rate_limit_remaining = response.headers.get('X-Ratelimit-Remaining')
rate_limit_reset = response.headers.get('X-Ratelimit-Reset')

print("Rate-Limit-Informationen:")
print(f"Verwendete Anfragen (X-Ratelimit-Used): {rate_limit_used}")
print(f"Verbleibende Anfragen (X-Ratelimit-Remaining): {rate_limit_remaining}")
print(f"Zurücksetzen des Limits in Sekunden (X-Ratelimit-Reset): {rate_limit_reset}")
