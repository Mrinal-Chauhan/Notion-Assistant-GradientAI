from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import sys
from pathlib import Path
import logging

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from agent.agent import NotionAgent

# Initialize NotionAgent instance
notion_agent = NotionAgent()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        logging.debug(f"Request body: {request.body}")
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logging.error("Invalid JSON received")
            return JsonResponse({'response': 'Invalid JSON'}, status=400)
        
        prompt = data.get('prompt', '').strip()
        if prompt:
            response = notion_agent.run(prompt)
            logging.debug(f"Agent response: {response}")
            return JsonResponse({'response': response})
        else:
            logging.warning("No prompt provided in the request")
            return JsonResponse({'response': 'No prompt provided'}, status=400)
    else:
        logging.warning("Invalid request method")
        return JsonResponse({'response': 'Invalid request method'}, status=400)
