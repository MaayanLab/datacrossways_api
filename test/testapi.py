import requests

url = 'http://127.0.0.1:5000/upload'
myobj = {'filename': 'testfile_x.txt'}
x = requests.post(url, json = myobj)
print(x.text)

url = 'http://127.0.0.1:5000/api/file/91'
x = requests.delete(url)
print(x.text)

url = 'http://127.0.0.1:5000/api/testkey'
x = requests.get(url, headers={"x-api-key": "dZVJBVHsmqBcEhhzn6JNNevUJMoYhyFk"})
print(x.text)

url = 'http://127.0.0.1:5000/api/i'
x = requests.get(url, headers={"x-api-key": "dZVJBVHsmqBcEhhzn6JNNevUJMoYhyFk"})
print(x.text)


url = 'http://127.0.0.1:5000/api/accesskey'
x = requests.get(url, headers={"x-api-key": "dZVJBVHsmqBcEhhzn6JNNevUJMoYhyFk"})
print(x.text)


url = 'http://127.0.0.1:5000/api/accesskey/1440'
x = requests.post(url, headers={"x-api-key": "dZVJBVHsmqBcEhhzn6JNNevUJMoYhyFk"})
print(x.text)



import time

tt = time.time()
r = requests.post('http://localhost:5000/api/file/search', json=query)
rr = r.json()
#print(rr)
time.time()-tt




url = 'http://localhost:5000/api/collection/1'
x = requests.get(url)
print(x.json())


query = {
    "offset": 0,
    "limit": 10,
    "query":{
        "creator": {
            "name": "c%"
        },
        "id": None
    }
}

import time

tt = time.time()
r = requests.post('http://localhost:5000/api/file/search', json=query)
rr = r.json()
#print(rr)
time.time()-tt



query = {
    "offset": 0,
    "limit": 10,
    "query":{
        "creator": {
            "name": "c1%"
        },
        "id": None
    }
}

import time

tt = time.time()
r = requests.post('http://localhost:5000/api/file/search', json=query)
rr = r.json()
#print(rr)
time.time()-tt




query = {
    "offset": 0,
    "limit": 10,
    "collection_id": 2,
    "owner_id": 1,
    "query":{
        "creator": {
            "name": "c1%"
        },
        "id": None
    }
}

import time

r = requests.post('https://lymecommons.org/api/file/search', json=query)
print(r.json())

import requests

query = {
    "offset": 0,
    "limit": 5,
    "file_info": "ile_1",
    "query":{
        "creator": {
            "name": "c1%"
        },
        "id": None
    }
}

r = requests.post('http://localhost:5000/api/file/search', json=query)
print(r.json())





query = {
    "first_name": "John",
    "last_name": "Doe",
    "name": "John Doe",
    "email": "john.doe@gmailo.com"
}

import time

tt = time.time()
r = requests.post('http://localhost:5000/api/user', json=query)
rr = r.json()
#print(rr)
time.time()-tt



query = {
    "first_name": "John",
    "last_name": "Doe",
    "name": "John Doe",
    "email": "john.doe@gmailo.com"
}

import time

tt = time.time()
r = requests.post('https://lymecommons.org/api/user', json=query)
rr = r.json()
print(rr)
time.time()-tt


url = 'https://lymecommons.org/api/user'
x = requests.get(url)
print(x.text)


url = 'https://lymecommons.org/api/user/file?offset=0&limit=10'
x = requests.get(url)
print(x.text)

url = 'http://localhost:5000/api/user/file?offset=0&limit=10'
x = requests.get(url)
print(x.text)



r = requests.delete('https://lymecommons.org/api/user/6')
print(r.json())


query = {
    "id": 7,
    "first_name": "John",
    "last_name": "Doe",
    "name": "John Doe the second",
    "email": "john.doe@gmailo2.com"
}

r = requests.patch('https://lymecommons.org/api/user', json=query)
print(r.json())




tt = time.time()
r = requests.delete('http://localhost:5000/api/user/4')
rr = r.json()
print(rr)
time.time()-tt





url = 'http://127.0.0.1:5000/api/user'
x = requests.get(url)
print(x.text)




url = 'http://127.0.0.1:5000/api/file/download/list/9,10,11'
x = requests.get(url)
print(x.text)



url = 'http://127.0.0.1:5000/api/file/metadata/14'
x = requests.get(url)
print(x.text)


url = 'http://127.0.0.1:5000/api/file/metadata/list/11,15,16'
x = requests.get(url)
print(x.text)

url = 'http://127.0.0.1:5000/api/file/15'
x = requests.get(url)
print(x.text)

curl "https://api.orcid.org/v3.0/0000-0002-1982-7652/person" -H "Authorization: Bearer 99e395b7-dce1-415d-93d9-eacc83e15e31"

curl "https://api.twitter.com/2/users/by/username/alexlachmann" -H "Authorization: Bearer AAAAAAAAAAAAAAAAAAAAAIwnlAEAAAAAL08H%2FYKMQzIM7T2VGp6uEBkfRYU%3DvEYgxnLSRPzHjsK4dfCdsQjU70XpMNwPYbIwlpYKHIL6m0iu1t"

curl "https://api.twitter.com/2/users/41147060/tweets?tweet.fields=created_at,public_metrics" -H "Authorization: Bearer AAAAAAAAAAAAAAAAAAAAAIwnlAEAAAAAL08H%2FYKMQzIM7T2VGp6uEBkfRYU%3DvEYgxnLSRPzHjsK4dfCdsQjU70XpMNwPYbIwlpYKHIL6m0iu1t"






import requests

query = {
    "first_name": "Delete",
    "last_name": "Me",
    "name": "Delete Me Please",
    "email": "john.doe@gmailo.com"
}

r = requests.post('http://localhost:5000/api/user', json=query)
print(r.json())


r = requests.delete('https://lymecommons.org/api/user/5')
print(r.json())

r = requests.get('http://localhost:5000/api/user/8', json=query)
print(r.json())


r = requests.get('http://localhost:5000/api/user')
print(r.json())




import requests

r = requests.get('http://localhost:5000/api/user/collection')
print(r.json())



import requests

r = requests.get('http://localhost:5000/api/user/storage')
print(r.json())

r = requests.get('http://localhost:5000/api/collection/1,2')
print(r.json())


import requests

r = requests.get('http://localhost:5000/api/file/10022')
print(r.json())





payload = {
    "filename": "test.fastq",
    "size": 200
}

base_url = "http://localhost:5000"
base_url = "https://lymecommons.org"



r = requests.post(base_url+'/api/file/startmultipart', json=payload).json()
print(r)

uuid = r["uuid"]
upload_id = r["upload_id"]

import io
with open("test/test.fastq", 'rb') as file:
    data = file.read()

file_name = "test.fastq"

part_size = 5 * 1024 * 1024
parts_count = len(data) // part_size + (len(data) % part_size != 0)

parts = []

for i in range(parts_count):
    part = io.BytesIO(data[i * part_size:(i + 1) * part_size])
    payload_part = {
      "filename": uuid + "/" + file_name,
      "upload_id": upload_id,
      "part_number": i+1,
    }
    rp = requests.post(base_url+'/api/file/signmultipart', json=payload_part).json()
    print(rp)
    rp2= requests.put(rp["url"], data=part)
    parts.append({"ETag": rp2.headers["ETag"].replace('"', ""), "PartNumber": i+1})
    print("ok:", i+1)


payload_complete = {
    "filename": uuid + "/" + file_name,
    "upload_id": upload_id,
    "parts": parts,
}
rc = requests.post(base_url+'/api/file/completemultipart', json=payload_complete).json()

rand = 'https://lymecommonsdev-dxw-vault.s3.amazonaws.com/3fkyomkxA3Vg/test.fastq?uploadId=3XqUlXfSFNlAe9v3d7VOZnbAtPr9eXiGhWTp47A0TVKN1I0YGJhB2fjg3M98QQy.eZrtZ0Fir3L8TzOu1uomVrZA4.nvrqjC9cIdEia1ADGWZdotyMfjm.OBwXwIquHt&partNumber=1&AWSAccessKeyId=AKIASN43LDMG63N4B54K&Signature=gzmruosaWMcBlmggREHzCPxUh%2Fw%3D&Expires=1676072603'

rand = "https://lymecommonsdev-dxw-vault.s3.amazonaws.com/3dLobXaSLgrP/test.JPG?uploadId=liM3LGXGT4e.36226WdDt6B4XmXXdv0yNskFBT4vOCpt_7AMeMwxEdqfGYgGaBe2dlOVFlKt6u.Bfba2Qh9yTJ5CQEKp9ZAByPC10aLUunab5xdZsA3SD8r8s5tULnx9&partNumber=2&AWSAccessKeyId=AKIASN43LDMG63N4B54K&Signature=u13pMQt9jTG%2BWAkn9ys6BUNJ6C0%3D&Expires=1676071707"
rp2= requests.put(rand, data=part)

base_url = "https://lymecommons.org"

payload = {
    "filename": "test.fastq",
    "size": 200
}

import requests

# Make a request to the "/upload" endpoint
response = requests.post(base_url + "/api/file/upload", json=payload)

# Extract the response as JSON
data = response.json()
print(data)
# Prepare the form data
formdata = {}
for key in data["response"]["fields"]:
    formdata[key] = data["response"]["fields"][key]

# Add the file to the form data
formdata["file"] = file

# Make a POST request with the form data
res = requests.post(data["response"]["url"], data=formdata)



payload = {
    "filename": "some new info",
    "user": "it's me Alex",
    "annotate_test": "working",
}

rc = requests.post(base_url+'/api/file/annotate/10620', json=payload).json()
print(rc)

rc = requests.get(base_url+'/api/collection/9').json()
print(rc)


payload = {
    "name": "empty_collection",
    "description": "This is a test collection",
    "files": ["would", "be", "ignored", "same with collections"]
}

rc = requests.post(base_url+'/api/collection/2', json=payload).json()
print(rc)



rc = requests.get(base_url+'/api/collection/1').json()
print(rc)


rc = requests.get(base_url+'/api/file/collection').json()
print(rc)


query = {
    "offset": 0,
    "limit": 10,
    "collection_id": 79,
    "query":{}
}

import time

r = requests.post('https://lymecommons.org/api/file/search', json=query)
print(r.json())


r = requests.get('https://lymecommons.org/api/collection/79/files')
print(r.json())

