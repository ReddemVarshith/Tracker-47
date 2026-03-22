from django.contrib import admin
from django.contrib.auth.models import User
from .models import Module, VideoLecture, Problem, UserProgress, Quiz, Question, Choice, QuizAttempt, QuestionResponse

class VideoLectureInline(admin.StackedInline):
    model = VideoLecture
    extra = 1

class ProblemInline(admin.StackedInline):
    model = Problem
    extra = 1

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    inlines = [VideoLectureInline, ProblemInline]

@admin.register(VideoLecture)
class VideoLectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module',)

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'difficulty', 'order', 'is_solved')
    list_filter = ('module', 'difficulty')
    actions = ['mark_as_solved', 'mark_as_unsolved']

    def is_solved(self, obj):
        try:
            user = User.objects.get(username='47')
            progress = UserProgress.objects.get(user=user)
            return progress.completed_problems.filter(id=obj.id).exists()
        except (User.DoesNotExist, UserProgress.DoesNotExist):
            return False
    is_solved.boolean = True
    is_solved.short_description = 'Solved'

    @admin.action(description='Mark selected problems as solved')
    def mark_as_solved(self, request, queryset):
        user, _ = User.objects.get_or_create(username='47')
        progress, _ = UserProgress.objects.get_or_create(user=user)
        for problem in queryset:
            progress.completed_problems.add(problem)
        self.message_user(request, f"Marked {queryset.count()} problems as solved.")

    @admin.action(description='Mark selected problems as unsolved')
    def mark_as_unsolved(self, request, queryset):
        user, _ = User.objects.get_or_create(username='47')
        progress, _ = UserProgress.objects.get_or_create(user=user)
        for problem in queryset:
            progress.completed_problems.remove(problem)
        self.message_user(request, f"Marked {queryset.count()} problems as unsolved.")

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'time_limit')
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'order')
    list_filter = ('quiz', 'question_type')
    inlines = [ChoiceInline]

class QuestionResponseInline(admin.StackedInline):
    model = QuestionResponse
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'text_answer')
    fields = ('question', 'selected_choice', 'text_answer', 'is_correct', 'is_reviewed', 'reviewer_comment')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total_questions', 'status', 'completed_at')
    list_filter = ('status', 'quiz')
    inlines = [QuestionResponseInline]
    readonly_fields = ('started_at', 'completed_at')

@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'attempt', 'is_correct', 'is_reviewed')
    list_filter = ('is_reviewed', 'is_correct', 'attempt__quiz')
    actions = ['approve_response', 'reject_response']

    @admin.action(description='Mark selected responses as CORRECT')
    def approve_response(self, request, queryset):
        for response in queryset:
            response.is_correct = True
            response.is_reviewed = True
            response.save()
            response.attempt.update_score()
        self.message_user(request, f"Approved {queryset.count()} responses and updated scores.")

    @admin.action(description='Mark selected responses as INCORRECT')
    def reject_response(self, request, queryset):
        for response in queryset:
            response.is_correct = False
            response.is_reviewed = True
            response.save()
            response.attempt.update_score()
        self.message_user(request, f"Rejected {queryset.count()} responses and updated scores.")

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user',)
