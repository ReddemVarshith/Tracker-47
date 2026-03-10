import requests
import json

url = 'http://127.0.0.1:8000/execute-code/' # need to find actual URL

data = {
    "language": "python",
    "code": "import sys\nprint('got:', sys.stdin.read())",
    "stdin": "hello world\n",
    "is_submission": False
}

print("Ready")
