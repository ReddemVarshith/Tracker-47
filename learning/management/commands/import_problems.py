import json
import os
from django.core.management.base import BaseCommand
from learning.models import Module, Problem

class Command(BaseCommand):
    help = 'Import DSA problems from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing problems')

    def handle(self, *args, **options):
        json_file_path = options['json_file']

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {json_file_path}"))
            return

        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading JSON: {str(e)}"))
            return

        module_title = data.get('module_title', 'General')
        module, created = Module.objects.get_or_create(title=module_title)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new module: {module_title}"))

        problems_data = data.get('problems', [])
        imported_count = 0

        for prob_data in problems_data:
            title = prob_data.get('title')
            difficulty = prob_data.get('difficulty', 'MEDIUM')
            description = prob_data.get('description', '')
            input_format = prob_data.get('input_format', '')
            output_format = prob_data.get('output_format', '')
            constraints = prob_data.get('constraints', [])
            sample_tests = prob_data.get('sample_tests', [])
            test_cases = prob_data.get('test_cases', [])

            problem, p_created = Problem.objects.get_or_create(
                module=module,
                title=title,
                defaults={
                    'difficulty': difficulty,
                    'description': description,
                    'input_format': input_format,
                    'output_format': output_format,
                    'constraints': constraints,
                    'sample_tests': sample_tests,
                    'test_cases': test_cases,
                }
            )

            if not p_created:
                # Update existing problem
                problem.difficulty = difficulty
                problem.description = description
                problem.input_format = input_format
                problem.output_format = output_format
                problem.constraints = constraints
                problem.sample_tests = sample_tests
                problem.test_cases = test_cases
                problem.save()
                self.stdout.write(f"Updated problem: {title}")
            else:
                self.stdout.write(self.style.SUCCESS(f"Imported new problem: {title}"))
            
            imported_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} problems into '{module_title}'"))
