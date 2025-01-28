# Getting your notion user id
import requests
import os
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_my_user_id():
    url = "https://api.notion.com/v1/users"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        users = response.json()["results"]
        for user in users:
            if user["object"] == "user":
                print(f"Name: {user['name']}, ID: {user['id']}")
    else:
        print(f"Error: {response.status_code}, {response.text}")

get_my_user_id()