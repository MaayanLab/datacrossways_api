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


