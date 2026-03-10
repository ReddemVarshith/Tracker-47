from django.db import models
from django.contrib.auth.models import User

class Module(models.Model):
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class VideoLecture(models.Model):
    module = models.ForeignKey(Module, related_name='lectures', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    video_url = models.URLField(blank=True, null=True)
    notes_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]
    module = models.ForeignKey(Module, related_name='problems', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    input_format = models.TextField(blank=True, null=True)
    output_format = models.TextField(blank=True, null=True)
    constraints = models.JSONField(default=list, blank=True)
    sample_tests = models.JSONField(default=list, blank=True)
    hidden_tests = models.JSONField(default=list, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='MEDIUM')
    order = models.IntegerField(default=0)
    test_cases = models.JSONField(default=list, blank=True, help_text="Combined for backend execution")

    class Meta:
        ordering = ['module', 'order']

    def __str__(self):
        return self.title

class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    completed_modules = models.ManyToManyField(Module, blank=True)
    completed_lectures = models.ManyToManyField(VideoLecture, blank=True)
    completed_problems = models.ManyToManyField(Problem, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Progress"


class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    language = models.CharField(max_length=50)
    passed_all_tests = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} ({'Pass' if self.passed_all_tests else 'Fail'})"
