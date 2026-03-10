import requests
import json
import urllib.request
from urllib.error import URLError

try:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/learning/execute_code/', # or whatever the url is
        data=json.dumps({
            "language": "python",
            "code": "import sys\nprint('Hello ' + sys.stdin.read().strip())",
            "stdin": "Varshith",
            "is_submission": False
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        print(res.read().decode())
except URLError as e:
    print(e)
