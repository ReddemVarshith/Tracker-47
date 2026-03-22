import random
from django.core.management.base import BaseCommand
from learning.models import Module, Quiz, Question, Choice

class Command(BaseCommand):
    help = 'Generates 30 questions (23 MCQ, 5 Descriptive, 2 Coding) for each module quiz'

    def handle(self, *args, **kwargs):
        modules = Module.objects.all()
        
        if not modules:
            self.stdout.write(self.style.ERROR("No modules found. Please create modules first."))
            return

        for module in modules:
            quiz, created = Quiz.objects.get_or_create(
                module=module,
                defaults={'title': f'Quiz for {module.title}', 'description': f'Test your knowledge on {module.title}'}
            )

            # Clear existing questions to avoid duplicates if re-run
            quiz.questions.all().delete()

            self.stdout.write(self.style.SUCCESS(f"Generating questions for module: {module.title}"))

            # 1. Generate 23 MCQs
            for i in range(1, 24):
                q = Question.objects.create(
                    quiz=quiz,
                    text=f"MCQ Question {i} for {module.title}: What is a key concept in this module?",
                    question_type='MCQ',
                    explanation=f"This is the explanation for MCQ {i} in {module.title}.",
                    order=i
                )
                # Create 4 choices for each MCQ
                for j in range(1, 5):
                    Choice.objects.create(
                        question=q,
                        text=f"Option {j} for MCQ {i}",
                        is_correct=(j == 1) # First option is correct for simplicity in generation
                    )

            # 2. Generate 5 Descriptive Questions
            for i in range(1, 6):
                Question.objects.create(
                    quiz=quiz,
                    text=f"Descriptive Question {i} for {module.title}: Explain the importance of a specific topic in {module.title}.",
                    question_type='DESCRIPTIVE',
                    explanation=f"Key points for the answer: Point A, Point B, Point C.",
                    order=23 + i
                )

            # 3. Generate 2 Coding Questions
            for i in range(1, 3):
                Question.objects.create(
                    quiz=quiz,
                    text=f"Coding Question {i} for {module.title}: Write a function to solve a basic problem related to {module.title}.",
                    question_type='CODING',
                    initial_code="def solution():\n    # Write your code here\n    pass",
                    expected_output="Expected output sequence",
                    explanation=f"The solution should handle edge cases and use optimal time complexity.",
                    order=28 + i
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully generated quizzes for {modules.count()} modules."))
