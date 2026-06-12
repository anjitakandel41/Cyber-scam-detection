from django.contrib import admin

from .models import Question, QuizAnswer, QuizAttempt


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'correct_option', 'is_active', 'updated_at')
    list_filter = ('is_active', 'correct_option')
    search_fields = ('text', 'option_a', 'option_b', 'option_c', 'option_d')
    fieldsets = (
        (None, {'fields': ('text', 'is_active')}),
        ('Options', {'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_option')}),
        ('Feedback', {'fields': ('explanation',)}),
    )


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'is_correct')
    can_delete = False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'total_questions', 'percentage', 'completed_at')
    list_filter = ('completed_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'score', 'total_questions', 'percentage', 'completed_at')
    inlines = [QuizAnswerInline]
