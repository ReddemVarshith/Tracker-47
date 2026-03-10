import requests
from django.core.management.base import BaseCommand
from learning.models import Module, Problem, VideoLecture
import re

class Command(BaseCommand):
    help = 'Loads DSA course content from Kunal Kushwaha GitHub repository'

    def handle(self, *args, **kwargs):
        from django.contrib.auth.models import User
        from learning.models import UserProgress
        
        user, created = User.objects.get_or_create(username="47", email="47@example.com")
        if created:
            user.set_password("47password")
            user.save()
            UserProgress.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS('Created user: 47'))

        self.stdout.write('Fetching data from GitHub assignments folder...')
        api_url = "https://api.github.com/repos/kunal-kushwaha/DSA-Bootcamp-Java/contents/assignments"
        
        headers = {'User-Agent': 'DSA-Platform'}
        response = requests.get(api_url, headers=headers)
        
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to fetch data: {response.status_code}'))
            self.load_fallback_data()
            return
            
        items = response.json()
        
        # Look for markdown files starting with numbers like 01-, 02-
        assignment_files = [item for item in items if item['type'] == 'file' and re.match(r'^\d{2}-.*\.md$', item['name'])]
        
        if not assignment_files:
            self.stdout.write(self.style.WARNING('No assignment files found via API. Using fallback data.'))
            self.load_fallback_data()
            return
            
        Module.objects.all().delete()
        Problem.objects.all().delete()
        VideoLecture.objects.all().delete()
        
        # Sort by file name for correct order
        assignment_files.sort(key=lambda x: x['name'])
        
        for index, file_item in enumerate(assignment_files):
            # Extract name: "01-flow-of-program.md" -> "Flow Of Program"
            raw_name = file_item['name']
            name = raw_name.replace('.md', '').replace('-', ' ').title()
            name = re.sub(r'^\d{2}\s', '', name)
            
            module = Module.objects.create(
                title=name,
                order=index + 1,
                description=f"Learn about {name} in Java"
            )
            self.stdout.write(f'Created Module: {module.title}')
            
            self.fetch_assignments(file_item['download_url'], module)
            
            # Add a placeholder video lecture
            VideoLecture.objects.create(
                module=module,
                title=f"Lecture: {name}",
                video_url="https://www.youtube.com/watch?v=rZ41y93P2Qo", # placeholder for course playlist
                order=1
            )
            
        self.stdout.write(self.style.SUCCESS('Successfully loaded DSA content!'))

    def fetch_assignments(self, url, module):
        try:
            res = requests.get(url)
            if res.status_code == 200:
                text = res.text
                lines = text.split('\n')
                order = 1
                found_any = False
                
                # State variables for block matching
                in_list = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Skip headings
                    if line.startswith('#'):
                        continue
                        
                    # Check for markdown list items (number. or -, *, +)
                    is_list_item = re.match(r'^(\d+\.|[-*+])\s+(.*)', line)
                    
                    if is_list_item:
                        content = is_list_item.group(2)
                        
                        # Check if it's a link [Title](URL)
                        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', content)
                        
                        if link_match:
                            title = link_match.group(1).strip()
                            link = link_match.group(2).strip()
                            
                            Problem.objects.create(
                                module=module,
                                title=title,
                                difficulty='MEDIUM',
                                order=order,
                                description=f"Solve the problem: {title}",
                                test_cases=[
                                    {"input": "5", "output": "Output for 5"},
                                    {"input": "10 20", "output": "Result is 30"}
                                ]
                            )
                        else:
                            # It's a plain text problem
                            # Clean up markdown bold/italic
                            title = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
                            title = re.sub(r'\*(.*?)\*', r'\1', title)
                            title = re.sub(r'`(.*?)`', r'\1', title)
                            
                            # Skip short generic lines that aren't problems
                            if len(title) > 10 and not title.lower().startswith('video'):
                                Problem.objects.create(
                                    module=module,
                                    title=(title[:100] + '...') if len(title) > 100 else title, # Truncate title
                                    difficulty='EASY',
                                    order=order,
                                    description=content,
                                    test_cases=[
                                        {"input": "3", "output": "Output for 3"},
                                        {"input": "-1", "output": "Invalid"}
                                    ]
                                )
                        order += 1
                        found_any = True
                return found_any
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to fetch assignments for {module.title}: {str(e)}"))
        return False

    def load_fallback_data(self):
        self.stdout.write('Loading fallback data...')
        Module.objects.all().delete()
        
        m1 = Module.objects.create(title="Flow of Program", order=1, description="Introduction to programming flow.")
        VideoLecture.objects.create(module=m1, title="Introduction to Web Development", video_url="https://www.youtube.com/watch?v=rZ41y93P2Qo", order=1)
        Problem.objects.create(module=m1, title="Input a year and find whether it is a leap year or not.", difficulty="EASY", order=1)
        Problem.objects.create(module=m1, title="Take two numbers and print the sum of both.", difficulty="EASY", order=2)
        
        m2 = Module.objects.create(title="First Java Course", order=2, description="Write your first Java program.")
        VideoLecture.objects.create(module=m2, title="First Java Program", video_url="https://www.youtube.com/watch?v=rZ41y93P2Qo", order=1)
        Problem.objects.create(module=m2, title="Write a program to print whether a number is even or odd.", difficulty="EASY", order=1)
        Problem.objects.create(module=m2, title="Take name as input and print a greeting message for that particular name.", difficulty="EASY", order=2)
        
        m3 = Module.objects.create(title="Conditionals and Loops", order=3, description="Master if-else and loops.")
        Problem.objects.create(module=m3, title="Area Of Circle Java Program", difficulty="MEDIUM", order=1)
        Problem.objects.create(module=m3, title="Area Of Triangle", difficulty="MEDIUM", order=2)
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded fallback content!'))
