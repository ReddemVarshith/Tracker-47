import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsa_platform.settings")
django.setup()

from django.test import Client

client = Client()

# Test 1: Compile error in Java
print("Testing Java syntax error...")
payload_java_error = {
    "language": "java",
    "code": "for \nimport java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n    }\n}",
    "problem_id": None, # no problem, just custom input
    "is_submission": False,
    "stdin": "1 2"
}
response = client.post('/api/execute-code/', data=json.dumps(payload_java_error), content_type='application/json')
print(response.status_code)
print(response.json())


# Test 2: Valid Java code
print("\nTesting Valid Java code...")
payload_java_valid = {
    "language": "java",
    "code": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int a = sc.nextInt();\n        int b = sc.nextInt();\n        System.out.print(a+b);\n    }\n}",
    "problem_id": None,
    "is_submission": False,
    "stdin": "1 2"
}
response2 = client.post('/api/execute-code/', data=json.dumps(payload_java_valid), content_type='application/json')
print(response2.status_code)
print(response2.json())

# Test 3: Valid Python code
print("\nTesting Valid Python code...")
payload_python_valid = {
    "language": "python",
    "code": "a, b = map(int, input().split())\nprint(a + b)",
    "problem_id": None,
    "is_submission": False,
    "stdin": "10 20"
}
response3 = client.post('/api/execute-code/', data=json.dumps(payload_python_valid), content_type='application/json')
print(response3.status_code)
print(response3.json())

# Test 4: Time Limit Exceeded (infinite loop) in Python
print("\nTesting TLE Python code...")
payload_python_tle = {
    "language": "python",
    "code": "while True: pass",
    "problem_id": None,
    "is_submission": False,
    "stdin": "10 20"
}
response4 = client.post('/api/execute-code/', data=json.dumps(payload_python_tle), content_type='application/json')
print(response4.status_code)
print(response4.json())

