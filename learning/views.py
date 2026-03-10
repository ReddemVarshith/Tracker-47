from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
import re
import requests
import tempfile
import subprocess
import os
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Module, Problem, VideoLecture, UserProgress, Submission

def get_user_47():
    # Helper to always get the profile for 47
    return User.objects.get(username='47')

def get_progress():
    user = get_user_47()
    progress, _ = UserProgress.objects.get_or_create(user=user)
    return progress

def dashboard(request):
    progress = get_progress()
    modules = Module.objects.all().prefetch_related('problems', 'lectures')
    
    total_problems = Problem.objects.count()
    completed_problems = progress.completed_problems.count()
    
    progress_percentage = 0
    if total_problems > 0:
        progress_percentage = int((completed_problems / total_problems) * 100)
    
    # Calculate progress per module
    modules_data = []
    for m in modules:
        m_total_probs = m.problems.count()
        m_completed = m.problems.filter(id__in=progress.completed_problems.all()).count()
        m_progress = int((m_completed / m_total_probs) * 100) if m_total_probs > 0 else 0
        modules_data.append({
            'module': m,
            'progress': m_progress,
            'is_completed': m_progress == 100
        })
        
    context = {
        'progress_percentage': progress_percentage,
        'completed_problems': completed_problems,
        'total_problems': total_problems,
        'modules_data': modules_data,
    }
    return render(request, 'learning/dashboard.html', context)

def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    progress = get_progress()
    
    problems = module.problems.all()
    completed_problems_ids = progress.completed_problems.values_list('id', flat=True)
    
    context = {
        'module': module,
        'lectures': module.lectures.all(),
        'problems': problems,
        'completed_problems_ids': list(completed_problems_ids),
    }
    return render(request, 'learning/module_detail.html', context)

def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    progress = get_progress()
    is_completed = progress.completed_problems.filter(id=problem.id).exists()
    
    # We will simulate explanation logic here
    explanation = f"Explanation for {problem.title}: Here we analyze the optimal approach to solve this algorithmic challenge. First, understand the variables. Then determine if it's a greedy approach, dynamic programming, or simple array manipulation. In Kunal's lectures, this is often driven by foundational concepts."
    
    submissions = Submission.objects.filter(user=progress.user, problem=problem).order_by('-submitted_at')

    context = {
        'problem': problem,
        'is_completed': is_completed,
        'explanation': explanation,
        'submissions': submissions,
    }
    return render(request, 'learning/problem_detail.html', context)

def toggle_problem_status(request, problem_id):
    if request.method == "POST":
        problem = get_object_or_404(Problem, id=problem_id)
        progress = get_progress()
        
        if progress.completed_problems.filter(id=problem.id).exists():
            progress.completed_problems.remove(problem)
            status = 'unsolved'
        else:
            progress.completed_problems.add(problem)
            status = 'solved'
            
        return JsonResponse({'status': 'success', 'problem_status': status})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@csrf_exempt
def execute_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            language = data.get('language', '')
            code = data.get('code', '')
            problem_id = data.get('problem_id')
            is_submission = data.get('is_submission', False)

            if language not in ('python', 'java', 'cpp', 'javascript'):
                return JsonResponse({"error": "Unsupported language"}, status=400)

            # Fetch problem for submission mode
            problem = None
            if problem_id:
                try:
                    problem = Problem.objects.get(id=int(problem_id))
                except (Problem.DoesNotExist, ValueError, TypeError):
                    pass

            results = []
            passed_all = True
            cases_to_run = []
            stdin_data = data.get('stdin', '')

            # 1. Add custom input case
            if stdin_data.strip():
                cases_to_run.append({
                    'input': stdin_data,
                    'output': None,
                    'is_custom': True,
                    'index': 'Custom'
                })

            # 2. Add problem test cases
            if problem:
                # 'Run Code' should test samples, 'Submit' should test everything
                tests_to_evaluate = problem.test_cases if is_submission else problem.sample_tests
                
                # If there is no custom input, we must evaluate the problem tests
                # If there IS custom input, we only evaluate problem tests if it's a submission
                if not stdin_data.strip() or is_submission:
                    for idx, tc in enumerate(tests_to_evaluate):
                        cases_to_run.append({
                            'input': tc.get('input', ''),
                            'output': tc.get('output', ''),
                            'is_custom': False,
                            'index': idx + 1
                        })

            with tempfile.TemporaryDirectory() as tmpdir:
                compilation_error = None
                src_path = None
                bin_path = None

                if language == 'python':
                    src_path = os.path.join(tmpdir, 'main.py')
                    with open(src_path, 'w') as f:
                        f.write(code)
                elif language == 'javascript':
                    src_path = os.path.join(tmpdir, 'main.js')
                    with open(src_path, 'w') as f:
                        f.write(code)
                elif language == 'cpp':
                    src_path = os.path.join(tmpdir, 'main.cpp')
                    bin_path = os.path.join(tmpdir, 'main')
                    with open(src_path, 'w') as f:
                        f.write(code)
                    compile_result = subprocess.run(
                        ['g++', '-o', bin_path, src_path],
                        capture_output=True, text=True, timeout=30
                    )
                    if compile_result.returncode != 0:
                        compilation_error = compile_result.stderr
                elif language == 'java':
                    # Rename public class to 'Main' and save as Main.java
                    java_src = re.sub(r'\bpublic\s+class\s+\w+', 'public class Main', code, count=1)
                    src_path = os.path.join(tmpdir, 'Main.java')
                    with open(src_path, 'w') as f:
                        f.write(java_src)
                    compile_result = subprocess.run(
                        ['javac', src_path],
                        capture_output=True, text=True, timeout=30
                    )
                    if compile_result.returncode != 0:
                        compilation_error = compile_result.stderr

                for test in cases_to_run:
                    expected_input  = test.get('input', '')
                    if expected_input is not None:
                        expected_input = str(expected_input)
                    else:
                        expected_input = ''
                    expected_output = test.get('output')
                    is_custom = test.get('is_custom', False)
                    tc_index = test.get('index')

                    stdout, stderr = '', ''

                    if compilation_error:
                        stderr = compilation_error
                        passed_all = False
                    else:
                        try:
                            if language == 'python':
                                run_res = subprocess.run(
                                    ['python3', src_path],
                                    input=expected_input, capture_output=True, text=True, timeout=5
                                )
                                stdout, stderr = run_res.stdout, run_res.stderr
                            elif language == 'javascript':
                                run_res = subprocess.run(
                                    ['node', src_path],
                                    input=expected_input, capture_output=True, text=True, timeout=5
                                )
                                stdout, stderr = run_res.stdout, run_res.stderr
                            elif language == 'cpp':
                                run_res = subprocess.run(
                                    [bin_path],
                                    input=expected_input, capture_output=True, text=True, timeout=5
                                )
                                stdout, stderr = run_res.stdout, run_res.stderr
                            elif language == 'java':
                                run_res = subprocess.run(
                                    ['java', '-cp', tmpdir, 'Main'],
                                    input=expected_input, capture_output=True, text=True, timeout=5
                                )
                                stdout, stderr = run_res.stdout, run_res.stderr
                        except subprocess.TimeoutExpired:
                            stderr = 'Time Limit Exceeded'
                            passed_all = False

                    actual = stdout.strip()
                    if is_custom:
                        passed = True if not stderr else False
                    else:
                        exp_out_strip = str(expected_output).strip() if expected_output is not None else ""
                        passed = (actual == exp_out_strip and not stderr)
                        if not passed:
                            passed_all = False

                    results.append({
                        "test_case": tc_index,
                        "input": expected_input,
                        "expected": str(expected_output).strip() if expected_output is not None else "N/A",
                        "actual": actual,
                        "stderr": stderr,
                        "passed": passed,
                        "is_custom": is_custom
                    })

            if is_submission and problem:
                user = get_user_47()
                # Log the submission
                Submission.objects.create(
                    user=user,
                    problem=problem,
                    code=code,
                    language=language,
                    passed_all_tests=passed_all
                )
                
                # Auto-solve if all tests passed
                if passed_all:
                    progress, _ = UserProgress.objects.get_or_create(user=user)
                    progress.completed_problems.add(problem)

            return JsonResponse({
                "is_submission": is_submission,
                "passed_all": passed_all,
                "results": results,
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)
