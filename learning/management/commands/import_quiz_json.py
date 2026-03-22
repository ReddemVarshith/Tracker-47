import json
from django.core.management.base import BaseCommand
from learning.models import Module, Quiz, Question, Choice

class Command(BaseCommand):
    help = 'Imports quiz questions from a JSON file (intended for ChatGPT output)'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')
        parser.add_argument('--module_id', type=int, help='Override module ID if not in JSON')

    def handle(self, *args, **options):
        file_path = options['json_file']
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read file: {e}"))
            return

        module_id = options.get('module_id') or data.get('module_id')
        if not module_id:
            self.stdout.write(self.style.ERROR("No module ID provided in command or JSON."))
            return

        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Module with ID {module_id} does not exist."))
            return

        # Get or create Quiz
        quiz, created = Quiz.objects.get_or_create(
            module=module,
            defaults={'title': f'Quiz for {module.title}', 'description': f'Test your knowledge on {module.title}'}
        )

        # Clear existing questions for a clean import
        quiz.questions.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Importing questions for: {module.title}"))

        questions_data = data.get('questions', [])
        for idx, q_data in enumerate(questions_data):
            q_text = q_data.get('text')
            q_type = q_data.get('type')
            explanation = q_data.get('explanation')
            
            # Create Question
            question = Question.objects.create(
                quiz=quiz,
                text=q_text,
                question_type=q_type,
                explanation=explanation,
                order=idx + 1,
                initial_code=q_data.get('initial_code', ''),
                expected_output=q_data.get('expected_output', '')
            )

            # Handle Choices for MCQ
            if q_type == 'MCQ':
                choices = q_data.get('choices', [])
                for c_data in choices:
                    Choice.objects.create(
                        question=question,
                        text=c_data.get('text'),
                        is_correct=c_data.get('is_correct', False)
                    )

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {len(questions_data)} questions."))
