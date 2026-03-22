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
class Quiz(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")

    def __str__(self):
        return f"Quiz for {self.module.title}"

class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice Question'),
        ('DESCRIPTIVE', 'Descriptive Question'),
        ('CODING', 'Coding Question'),
    ]
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    explanation = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    # For coding questions
    initial_code = models.TextField(blank=True, null=True)
    expected_output = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.get_question_type_display()}: {self.text[:50]}"

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('PENDING_REVIEW', 'Pending Review'),
        ('COMPLETED', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    random_seed = models.IntegerField(default=0, help_text="Seed for consistent MCQ randomization")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s attempt at {self.quiz.module.title} ({self.status})"

    def update_score(self):
        """Recalculates the score based on reviewed responses."""
        self.score = self.responses.filter(is_correct=True).count()
        # If all questions are reviewed, mark as completed
        if not self.responses.filter(is_reviewed=False).exists():
            self.status = 'COMPLETED'
        else:
            self.status = 'PENDING_REVIEW'
        self.save()

class QuestionResponse(models.Model):
    attempt = models.ForeignKey(QuizAttempt, related_name='responses', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    reviewer_comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Response to {self.question.text[:20]}"
