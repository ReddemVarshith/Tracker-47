from django.contrib import admin
from .models import Module, VideoLecture, Problem, UserProgress

class VideoLectureInline(admin.StackedInline):
    model = VideoLecture
    extra = 1

class ProblemInline(admin.StackedInline):
    model = Problem
    extra = 1

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    inlines = [VideoLectureInline, ProblemInline]

@admin.register(VideoLecture)
class VideoLectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module',)

from django.contrib.auth.models import User

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

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user',)
