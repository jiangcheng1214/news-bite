import requests

url = 'http://54.158.154.121:6000/data/tweets/finance/20230513/raw_0'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJpYW0uYXBpLm1hcm1vdGVkdS5jb20iLCJleHAiOjE2ODQwNTY5OTcsImlkZW50aXR5IjoiYWRtaW4iLCJpc3MiOiJpYW0tYXBpc2VydmVyIiwib3JpZ19pYXQiOjE2ODM5NzA1OTcsInN1YiI6ImFkbWluIn0.14Yb0ay5Cnsd96UXPu_AodX9E-9NLNVd6j8t-cnYjkI',
}

response = requests.get(url, headers=headers)

# 打印响应内容
print(response.text)
