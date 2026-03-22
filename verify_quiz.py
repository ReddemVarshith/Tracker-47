import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dsa_platform.settings')
django.setup()

from learning.models import Module, Quiz, Question, Choice, QuizAttempt, QuestionResponse
from django.contrib.auth.models import User

def verify():
    print("--- Quiz Verification ---")
    
    # 1. Check Modules and Quizzes
    modules = Module.objects.all()
    print(f"Total Modules: {modules.count()}")
    
    for module in modules:
        try:
            quiz = module.quiz
            q_count = quiz.questions.count()
            print(f"Module '{module.title}': Quiz exists with {q_count} questions.")
            
            # Check question types
            mcq_count = quiz.questions.filter(question_type='MCQ').count()
            desc_count = quiz.questions.filter(question_type='DESCRIPTIVE').count()
            code_count = quiz.questions.filter(question_type='CODING').count()
            print(f"  - MCQs: {mcq_count}, Descriptive: {desc_count}, Coding: {code_count}")
            
            if q_count != 30:
                print(f"  [WARNING] Question count mismatch! Expected 30, got {q_count}")
            
            # Check MCQs for choices
            mcqs_without_choices = quiz.questions.filter(question_type='MCQ', choices=None).count()
            if mcqs_without_choices > 0:
                print(f"  [ERROR] Found {mcqs_without_choices} MCQs without choices!")
                
        except Quiz.DoesNotExist:
            print(f"  [ERROR] Module '{module.title}' has no quiz!")

    # 2. Check for at least one attempt (if exists)
    attempts = QuizAttempt.objects.all()
    print(f"\nTotal Quiz Attempts: {attempts.count()}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify()
