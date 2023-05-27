from urllib.parse import urlencode

import requests


class TwitterUserLooker:

    def __init__(self, api_key: str):
        self.api_key = api_key

    def lookup_user_metadata(self, userId):
        URLParamsString = urlencode({
            'user.fields': 'id,description,location,created_at,name,username,verified,protected,public_metrics,url',
            'ids': userId
        })
        url = 'https://api.twitter.com/2/users?' + URLParamsString
        response = requests.get(
            url, headers={'authorization': f'Bearer {self.api_key}'})
        responseJson = response.json()
        jsonData = responseJson['data']
        return jsonData[0]
