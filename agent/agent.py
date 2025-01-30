import openai
import os
import sys
import inspect
import json
from dotenv import load_dotenv
from pathlib import Path
from agent.sysprompt import SYSTEM_PROMPT


# Add the project root to Python path for Django to work
sys.path.append(str(Path(__file__).resolve().parent))
from tools.notion import NotionClient


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")


class NotionAgent:

    def __init__(self): 
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.thread = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.model = "gpt-4o-mini-2024-07-18"
        self.notion = NotionClient()

        # Define tools
        self.tools = [self.notion.get_data]
        self.tools_schema = [self.function_to_schema(tool) for tool in self.tools]
        self.tools_map = {tool.__name__: tool for tool in self.tools}


    def function_to_schema(self, func) -> dict:
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            type(None): "null",
        }

        def get_type(annotation):
            if annotation == list:
                return {"type": "array", "items": {"type": "string"}}  # Default item to string
            if annotation == dict:
                return {"type": "object"}
            return {"type": type_map.get(annotation, "string")}

        try:
            signature = inspect.signature(func)
        except ValueError as e:
            raise ValueError(
                f"Failed to get signature for function {func.__name__}: {str(e)}"
            )

        parameters = {}
        for param in signature.parameters.values():
            param_type = get_type(param.annotation)
            parameters[param.name] = param_type

        required = [
            param.name
            for param in signature.parameters.values()
            if param.default == inspect._empty
        ]

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": (func.__doc__ or "").strip(),
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                },
            },
        }



    def get_response(self, prompt):
        
        self.thread.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.thread,
            tools=self.tools_schema
        )

        message = response.choices[0].message
        return message


    def execute_tool(self, tool_call):

        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "get_data":

            result = self.tools_map[function_name](**arguments)
            self.thread.append({"role": "tool", "tool_call_id" : tool_call.id, "content": str(result)})

            if len(result) == 1:
                prompt = f"""
                The user has the following tasks in their notion:
                {result['Tasks']}

                Help the user to boost their productivity however you feel, If you feel like you need more information, ask the user. Or If required, you can make a detailed plan for the user.

                The user prompt is {self.thread[-3]["content"]}
                """
            elif len(result) == 2:
                prompt = f"""
                The user has the following projects:
                {result['Projects']}
                The user has the following tasks:
                {result['Tasks']}

                Help the user to boost their productivity however you feel, If you feel like you need more information, ask the user. Or If required, you can make a detailed plan for the user.

                The user prompt is {self.thread[-3]["content"]}
                """
            else:
                return None    

            message = self.get_response(prompt)
            self.thread.append({"role": "assistant", "content": message.content})
            return message.content


    def run(self, prompt):
        message = self.get_response(prompt)

        if message.tool_calls:
            self.thread.append(message)
            for tool_call in message.tool_calls:
                result = self.execute_tool(tool_call)
                return result
        
        self.thread.append({"role": "assistant", "content": message.content})
        return message.content
