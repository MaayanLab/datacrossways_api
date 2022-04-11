import requests

url = 'http://127.0.0.1:5000/upload'
myobj = {'filename': 'testfile_x.txt'}
x = requests.post(url, json = myobj)
print(x.text)

