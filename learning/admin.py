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

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'difficulty', 'order')
    list_filter = ('module', 'difficulty')

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user',)
