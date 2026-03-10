import json
import argparse
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Loads problem JSON data into the Neon DB dsa_problems_bank table'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file to load')

    def handle(self, *args, **kwargs):
        json_file_path = kwargs['json_file']

        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read JSON file: {e}"))
            return

        if isinstance(data, dict) and 'problems' in data:
            data = data['problems']

        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR("JSON data must be a list of problem objects."))
            return

        query = """
        INSERT INTO dsa_problems_bank (
            id, title, module, description, input_format, output_format, constraints, sample_tests, hidden_tests, hints
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            module = EXCLUDED.module,
            description = EXCLUDED.description,
            input_format = EXCLUDED.input_format,
            output_format = EXCLUDED.output_format,
            constraints = EXCLUDED.constraints,
            sample_tests = EXCLUDED.sample_tests,
            hidden_tests = EXCLUDED.hidden_tests,
            hints = EXCLUDED.hints;
        """

        inserted_count = 0
        with connection.cursor() as cursor:
            for item in data:
                try:
                    cursor.execute(query, [
                        item.get('id'),
                        item.get('title', ''),
                        item.get('module', ''),
                        item.get('description', ''),
                        item.get('input_format', ''),
                        item.get('output_format', ''),
                        json.dumps(item.get('constraints', [])),
                        json.dumps(item.get('sample_tests', [])),
                        json.dumps(item.get('hidden_tests', [])),
                        json.dumps(item.get('hints', []))
                    ])
                    inserted_count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Failed to insert problem {item.get('id')}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {inserted_count} problems into dsa_problems_bank."))
