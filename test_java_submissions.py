import requests
import json
import sqlite3

def test_all():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, sample_tests, test_cases FROM learning_problem")
    problems = cursor.fetchall()
    
    for p_id, title, sample, tests in problems:
        payload = {
            "language": "java",
            "code": "public class Main { public static void main(String[] args) {} }",
            "problem_id": p_id,
            "is_submission": True,
            "stdin": ""
        }
        try:
            r = requests.post('http://127.0.0.1:8000/api/execute-code/', json=payload)
            if r.status_code == 500:
                print(f"Problem {p_id} ({title}) caused 500 Error: {r.text[:200]}")
            else:
                try:
                    r.json()
                except Exception as e:
                    print(f"Problem {p_id} returned non-JSON: {r.text[:200]}")
        except Exception as e:
            print(f"Error on problem {p_id}: {e}")

if __name__ == '__main__':
    test_all()
