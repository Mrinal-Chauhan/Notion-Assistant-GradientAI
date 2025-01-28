from dotenv import load_dotenv
import os
import requests

class NotionClient:
    
    def __init__(self):

        # Change the default encoding to utf-8
        import sys,io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        # Load the environment variables
        load_dotenv()
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_projects = os.getenv("DATABASE_PROJECTS")
        self.database_tasks = os.getenv("DATABASE_TASKS")
        self.userid = os.getenv("NOTION_USER_ID")

        # Set up the headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        
    def get_database(self, database_id):
        
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        response = requests.post(url, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None


    def parse_database_projects(self, database_data):

        parsed_data = []

        if database_data:

            for page in database_data.get("results", []):

                project_data = {}
                properties = page.get("properties", {})
                
                for prop_name, prop_value in properties.items():

                    # Handling different property types in Notion

                    if prop_name == 'Project name':
                        project_data[prop_name] = prop_value['title'][0]['text']['content']

                    elif prop_name == 'Owner':
                        pass

                    elif prop_name == 'Status':
                        project_data[prop_name] = prop_value['status']['name']

                    elif prop_name == 'Completion':
                        project_data[prop_name] = prop_value['rollup']['number']

                    elif prop_name == 'Priority':
                        project_data[prop_name] = prop_value['select']['name']

                    elif prop_name == 'Dates':
                        project_data[prop_name] = prop_value['date']['start']

                    elif prop_name == 'Summary':
                        project_data[prop_name] = prop_value['rich_text'][0]['text']['content']

                    elif prop_name == 'Tasks':
                        pass

                    else:
                        project_data[prop_name] = prop_value

                parsed_data.append(project_data)

        return parsed_data


    def parse_database_tasks(self, database_data):
        
        parsed_data = []

        if database_data:

            for page in database_data.get("results", []):

                task_data = {}
                properties = page.get("properties", {})
                
                for prop_name, prop_value in properties.items():

                    # Handling different property types in Notion (title, rich text, etc.)

                    if prop_name == 'Task name':
                        task_data[prop_name] = prop_value['title'][0]['text']['content']

                    elif prop_name == 'Status':
                        task_data[prop_name] = prop_value['status']['name']

                    elif prop_name == 'Assignee':
                        pass

                    elif prop_name == 'Due':
                        task_data[prop_name] = prop_value['date']['start']
                    
                    elif prop_name == 'Priority':
                        task_data[prop_name] = prop_value['select']['name']
                    
                    elif prop_name == 'Projects':
                        pass

                    else:
                        task_data[prop_name] = prop_value

                parsed_data.append(task_data)

        return parsed_data


    def get_data(self, database_names: list):
        """
            Fetches data from the specified Notion database.

            Parameters:
            database_names (list): The names of the Notion databases to fetch data from. Possible values are ['Projects'] or ['Tasks'] or ['Projects','Tasks'].

            Returns:
            dict: A dictionary containing the parsed data from the specified databases.

            Examples:
            >>> data = get_data(['Projects'])
            >>> print(data)
            [
                {
                    'Project name': 'Project 1', 
                    'Status': 'In progress', 
                    'Completion': 0.5, 
                    'Priority': 'High', 
                    'Dates': '2024-05-16', 
                    'Summary': 'No content'
                }
            ]
            
            >>> data = get_data(['Tasks'])
            >>> print(data)
            [
                {
                    'Task name': 'Task 1', 
                    'Status': 'Done', 
                    'Due': '2024-05-29', 
                    'Priority': 'Low'} 
                }
            ]
            """

        data_databases = {}
        
        for database_name in database_names:
            
            if database_name == "Projects":
                data = self.get_database(database_id = self.database_projects)
                parsed_data = self.parse_database_projects(data)
                data_databases['Projects'] = parsed_data

            elif database_name == "Tasks": 
                data = self.get_database(database_id = self.database_tasks)
                parsed_data = self.parse_database_tasks(data)
                data_databases['Tasks'] = parsed_data

            else:
                return None                

        return data_databases



    def add_entry(self, database_name, data):

        if database_name == "Projects":
            database_id = self.database_projects
        elif database_name == "Tasks":
            database_id = self.database_tasks
        else:
            return None
        

        if database_name == "Projects":

            # Build the payload based for projects database
            payload = {
                "parent": {
                    "database_id": self.database_projects
                },
                
                "properties": {
                    "Project name": {
                        "title": [
                            {
                                "text": {
                                    "content": data.get("Name")
                                }
                            }
                        ]
                    },

                    "Owner": {  
                        "people": [
                            {
                                "id": self.userid  
                            }
                        ]
                    },

                    "Status": {
                        "status": {
                            "name": data.get("Status")  
                        }
                    },

                    "Priority": {
                        "select": {
                            "name": data.get("Priority")  
                        }
                    },

                    "Dates": {
                        "date": {
                            "start": data.get("Date_Start"),
                            "end": data.get("Date_End")
                        }
                    },

                    "Summary": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": data.get("Summary")
                                }
                            }
                        ]
                    },
                }
            }

        if database_name == "Tasks":
            pass

        url = f"https://api.notion.com/v1/pages"

        # Send the request to create the page
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            print("Entry added successfully!")
            return response.json() 
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
