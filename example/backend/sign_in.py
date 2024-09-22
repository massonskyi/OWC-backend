import requests

url = "http://localhost:8000/api/auth/sign_in"

headers = {
    'accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}

data = {
    'username': 'username',
    'password': 'password or hash_password',
}

response = requests.post(url, headers=headers, data=data)
print(response.json())
