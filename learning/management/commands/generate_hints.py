"""
Management command to assign generic hints to existing problems.
"""

from django.core.management.base import BaseCommand
from learning.models import Problem


def generate_hints(title):
    title_lower = title.lower()
    
    hints = [
        f"Start by carefully reading the requirements for '{title}'. What are the input constraints?",
        "Consider manually tracing an example test case on paper. What patterns emerge?"
    ]
    
    if "string" in title_lower or "substring" in title_lower:
        hints.append("Since this involves strings, consider if a two-pointer approach or sliding window would be beneficial.")
    elif "array" in title_lower or "list" in title_lower:
        hints.append("For arrays, sorting the data first or using a hash map to track elements are common initial strategies.")
    elif "tree" in title_lower:
        hints.append("Tree problems are usually best solved recursively. Have you considered Breadth-First or Depth-First Search?")
    elif "binary" in title_lower:
        hints.append("Think about bit manipulation techniques, or if it's a search space, binary search might be the optimal path.")
    elif sum(1 for word in ["sort", "search", "find", "maximum", "minimum"] if word in title_lower) > 0:
        hints.append("Does the problem require an optimal O(n log n) or O(n) solution? Check if you are doing redundant work.")
        
    hints.append("If you are stuck, try a brute force solution first to guarantee a correct answer, then optimize it.")
    return hints


class Command(BaseCommand):
    help = "Generates default generic hints for problems missing hints."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing hints",
        )

    def handle(self, *args, **options):
        force = options["force"]

        qs = Problem.objects.all() if force else Problem.objects.filter(hints=[])

        total = qs.count()
        generated = 0

        self.stdout.write(f"Generating hints for {total} problems...")

        for problem in qs:
            problem.hints = generate_hints(problem.title)
            problem.save(update_fields=["hints"])
            generated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Assigned hints to {generated} problems."
            )
        )
