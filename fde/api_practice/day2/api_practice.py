import requests
import pandas as pd

url="https://jsonplaceholder.typicode.com/users"

response=requests.get(url)
print("Status Code:", response.status_code)

data=response.json()

print("\nsample record:")
print(data[0])