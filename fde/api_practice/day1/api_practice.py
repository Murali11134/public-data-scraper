import requests
import pandas as pd

# API URL
url = "https://jsonplaceholder.typicode.com/posts"

# Query parameters
params = {
    "userId": 1
}

# Headers
headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

try:
    # Send GET request
    response = requests.get(url, params=params, headers=headers, timeout=10)

    # Print status code
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        # Convert JSON to Python object
        data = response.json()

        print("\nFirst record:")
        print(data[0])

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Save to CSV
        df.to_csv("fde/api_practice/day1/output.csv", index=False)

        print("\nSaved to output.csv")
        print("Number of records:", len(df))

    else:
        print("Request failed:", response.text)

except Exception as e:
    print("Error:", e)