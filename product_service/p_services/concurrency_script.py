import requests
from concurrent.futures import ThreadPoolExecutor


def update_product(data):
    url = "http://127.0.0.1:5002/api/products/4"
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MjA3MTc1OTF9.vAKVBozm7m9A-NjtErIWUZ8e70H0ZXJDPnCulAeE1zs'}
    response = requests.put(url, json=data, headers=headers)
    print(response.status_code, response.json())
    return response.json()


if __name__ == "__main__":
    data = [{
        "name": "Updated Product112",
        "description": "First user update112",
        "price": 1.00,
        "stock": 1,
        "version": 13
    }, {
        "name": "Updated Product321",
        "description": "Second user update321",
        "price": 1931.00,
        "stock": 12301,
        "version": 13
    }]  # Different stock values for concurrent updates

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [executor.submit(update_product, stock)
                   for stock in data]

    for future in results:
        try:
            data = future.result()
            print("data", data)
        except Exception as exc:
            print(f'Generated an exception: {exc}')
