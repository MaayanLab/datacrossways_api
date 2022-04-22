import requests
import json
import os


res = requests.put(signed_url, data=file_chunk)
    print(res.request.headers)
