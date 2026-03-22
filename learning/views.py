from django.shortcuts import render, get_object_or_404, redirect
from functools import wraps
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
import json
import re
import requests
import tempfile
import subprocess
import os
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import random
from .models import Module, Problem, VideoLecture, UserProgress, Submission, Quiz, Question, Choice, QuizAttempt, QuestionResponse

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
    user = get_user_47()
    for m in modules:
        m_total_probs = m.problems.count()
        m_completed = m.problems.filter(id__in=progress.completed_problems.all()).count()
        m_progress = int((m_completed / m_total_probs) * 100) if m_total_probs > 0 else 0
        
        # Get latest quiz attempt
        latest_attempt = QuizAttempt.objects.filter(user=user, quiz__module=m).order_by('-completed_at').first()
        
        modules_data.append({
            'module': m,
            'progress': m_progress,
            'is_completed': m_progress == 100,
            'quiz_score': latest_attempt.score if latest_attempt else None,
            'quiz_total': latest_attempt.total_questions if latest_attempt else None,
            'quiz_status': latest_attempt.status if latest_attempt else None,
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

def module_quiz(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    quiz = get_object_or_404(Quiz, module=module)
    questions = quiz.questions.all().prefetch_related('choices')
    
    # Generate a random seed for this attempt
    random_seed = random.randint(1, 1000000)
    
    # Shuffle choices for MCQ questions in memory using the seed
    for question in questions:
        if question.question_type == 'MCQ':
            choices = list(question.choices.all())
            # Use a local Random instance with the seed to be deterministic within this view
            # We add question.id to the seed so different questions have different shuffles
            q_random = random.Random(random_seed + question.id)
            q_random.shuffle(choices)
            question.randomized_choices = choices
    
    context = {
        'module': module,
        'quiz': quiz,
        'questions': questions,
        'random_seed': random_seed,
    }
    return render(request, 'learning/quiz_detail.html', context)

@csrf_exempt
def quiz_submit(request, module_id):
    if request.method == 'POST':
        module = get_object_or_404(Module, id=module_id)
        quiz = get_object_or_404(Quiz, module=module)
        user = get_user_47()
        
        try:
            data = json.loads(request.body)
            answers = data.get('answers', {})
            random_seed = data.get('random_seed', 0)
            
            attempt = QuizAttempt.objects.create(
                user=user, 
                quiz=quiz, 
                total_questions=quiz.questions.count(),
                random_seed=random_seed,
                status='COMPLETED' # Default to completed, changed below if needed
            )
            
            score = 0
            has_subjective = False
            for q_id, answer in answers.items():
                try:
                    question = Question.objects.get(id=int(q_id), quiz=quiz)
                    response = QuestionResponse(attempt=attempt, question=question)
                    
                    if question.question_type == 'MCQ':
                        choice = Choice.objects.get(id=int(answer), question=question)
                        response.selected_choice = choice
                        response.is_reviewed = True # MCQs are auto-reviewed
                        if choice.is_correct:
                            response.is_correct = True
                            score += 1
                    else:
                        response.text_answer = answer
                        response.is_reviewed = False # Subjective needs manual review
                        response.is_correct = False # Not correct until reviewed
                        has_subjective = True
                    
                    response.save()
                except (Question.DoesNotExist, Choice.DoesNotExist, ValueError):
                    continue
            
            attempt.score = score
            if has_subjective:
                attempt.status = 'PENDING_REVIEW'
            attempt.save()
            
            return JsonResponse({'status': 'success', 'attempt_id': attempt.id})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    # Redirect if attempt is still pending review
    if attempt.status == 'PENDING_REVIEW':
        return redirect('learning:quiz_history')
        
    responses = attempt.responses.all().select_related('question', 'selected_choice').prefetch_related('question__choices')
    
    # Deterministically shuffle choices for each question based on the attempt's seed
    for resp in responses:
        if resp.question.question_type == 'MCQ':
            choices = list(resp.question.choices.all())
            q_random = random.Random(attempt.random_seed + resp.question.id)
            q_random.shuffle(choices)
            resp.question.randomized_choices = choices
    
    # Calculate score percentage
    percentage = (attempt.score / attempt.total_questions * 100) if attempt.total_questions > 0 else 0
    
    context = {
        'attempt': attempt,
        'responses': responses,
        'percentage': int(percentage),
    }
    return render(request, 'learning/quiz_results.html', context)

def quiz_history(request):
    user = get_user_47()
    attempts = QuizAttempt.objects.filter(user=user).order_by('-completed_at').select_related('quiz__module')
    return render(request, 'learning/quiz_history.html', {'attempts': attempts})

# Admin Portal Password (can be moved to settings.py for production)
ADMIN_PORTAL_PASSWORD = "admin47"

def admin_portal_required(view_func):
    """Decorator that ensures the user has entered the admin portal password."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('learning:dashboard')
        
        # Check if auth exists
        if not request.session.get('admin_portal_auth'):
            # Store the intended URL to redirect back after login
            request.session['admin_login_next'] = request.get_full_path()
            return redirect('learning:admin_login')
        
        # Determine if it's an AJAX request (e.g., from the review actions)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
                  request.content_type == 'application/json'
        
        # Call the view
        result = view_func(request, *args, **kwargs)
        
        # If it's a full page load, clear the auth so next navigation asks again
        if not is_ajax:
            request.session['admin_portal_auth'] = False
            
        return result
    return _wrapped_view

@staff_member_required
def admin_login(request):
    """View for the admin portal password page."""
    error = None
    if request.method == 'POST':
        entered_password = request.POST.get('admin_password')
        if entered_password == ADMIN_PORTAL_PASSWORD:
            request.session['admin_portal_auth'] = True
            next_url = request.session.pop('admin_login_next', 'learning:admin_quiz_list')
            try:
                # Try to resolve if it's a URL name, otherwise use as raw URL
                return redirect(next_url)
            except:
                return redirect('learning:admin_quiz_list')
        else:
            error = "Incorrect portal password. Please try again."
    
    return render(request, 'learning/admin_login.html', {'error': error})

@admin_portal_required
def admin_quiz_list(request):
    """Lists all quiz attempts that have pending subjective answers."""
    pending_attempts = QuizAttempt.objects.filter(status='PENDING_REVIEW').order_by('-completed_at')
    context = {
        'attempts': pending_attempts
    }
    return render(request, 'learning/admin_quiz_list.html', context)

@admin_portal_required
def admin_quiz_review(request, attempt_id):
    """Detailed view for reviewing subjective answers of a specific attempt."""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    pending_responses = attempt.responses.filter(
        question__question_type__in=['DESCRIPTIVE', 'CODING'],
        is_reviewed=False
    ).select_related('question')
    
    reviewed_responses = attempt.responses.filter(
        question__question_type__in=['DESCRIPTIVE', 'CODING'],
        is_reviewed=True
    ).select_related('question')
    
    # Deterministically shuffle choices for all MCQ questions in this attempt
    all_responses = attempt.responses.all().select_related('question').prefetch_related('question__choices')
    for resp in all_responses:
        if resp.question.question_type == 'MCQ':
            choices = list(resp.question.choices.all())
            q_random = random.Random(attempt.random_seed + resp.question.id)
            q_random.shuffle(choices)
            resp.question.randomized_choices = choices

    context = {
        'attempt': attempt,
        'pending_responses': pending_responses,
        'reviewed_responses': reviewed_responses,
        'all_responses_with_randomized_choices': all_responses # Optional, but helps if we need MQCs later
    }
    return render(request, 'learning/admin_quiz_review.html', context)

@csrf_exempt
@admin_portal_required
def admin_review_action(request):
    """AJAX endpoint to approve or reject a specific response."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            response_id = data.get('response_id')
            action = data.get('action') # 'approve' or 'reject'
            comment = data.get('comment', '')
            
            response = get_object_or_404(QuestionResponse, id=response_id)
            
            if action == 'approve':
                response.is_correct = True
            else:
                response.is_correct = False
                
            response.is_reviewed = True
            response.reviewer_comment = comment
            response.save()
            
            # Update the attempt score and status
            response.attempt.update_score()
            
            return JsonResponse({
                'status': 'success',
                'is_correct': response.is_correct,
                'new_score': response.attempt.score,
                'attempt_completed': response.attempt.status == 'COMPLETED'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
