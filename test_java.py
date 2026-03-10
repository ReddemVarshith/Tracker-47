import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dsa_platform.settings')
django.setup()

from learning.models import Problem

for p in Problem.objects.all():
    payload = {
        "language": "java",
        "code": "public class Main { public static void main(String[] args) {} }",
        "problem_id": p.id,
        "is_submission": True,
        "stdin": ""
    }
    try:
        r = requests.post('http://127.0.0.1:8000/api/execute-code/', json=payload)
        if r.status_code == 500:
            print(f"Problem {p.id} ({p.title}) caused 500 Error!")
        else:
            try:
                r.json()
            except Exception as e:
                print(f"Problem {p.id} returned non-JSON!")
    except Exception as e:
        print(f"Error on problem {p.id}: {e}")
