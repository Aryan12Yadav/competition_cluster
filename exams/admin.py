# FILE: exams/admin.py

from django.contrib import admin
# Ensure all models are imported correctly
from .models import ExamCategory, MockTest, Testimonial, Question, Option, TestResult, UserAnswer, Subject 

# This inline allows you to add Options directly when editing a Question.
class OptionInline(admin.TabularInline):
    model = Option
    extra = 4  # Provides 4 empty slots for options.
    max_num = 4 # Limits the number of options to 4.

# This inline allows you to add Questions (and their Options) from the Mock Test page.
class QuestionInline(admin.StackedInline):
    model = Question
    # Provide code with comments: Nested inline for Options
    inlines = [OptionInline] 
    extra = 1 # Provides 1 empty slot for a new question.
    # Provide code with comments: Fields displayed in the Question admin form
    fields = ('subject', 'text', 'difficulty', 'marks', 'negative_marks', 'solution')

@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    # Provide code with comments: Fields shown in the list display
    list_display = ('name', 'slug')
    
    # CRITICAL FIX: The redundant 'fields' attribute that caused the FieldError is REMOVED.
    # Django now loads only the editable fields in the form.
    
    # Provide code with comments: Automatically generates slug from the name field
    # prepopulated_fields = {'slug': ('name',)}

@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'question_count', 'is_free', 'is_new')
    list_filter = ('category', 'is_free', 'is_new')
    search_fields = ('title',)
    # Provide code with comments: Adds the powerful Question editor to this page.
    inlines = [QuestionInline]

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'is_featured')
    list_filter = ('is_featured',)

# This is the new, enhanced admin for your Test Results.
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    # Defines the columns shown in the list view.
    list_display = ('user', 'mock_test', 'score', 'percentage_display', 'end_time')
    
    # Adds a filter sidebar for these fields.
    list_filter = ('mock_test', 'user')
    
    # Adds a search bar that searches these fields.
    search_fields = ('user__username', 'mock_test__title')
    
    # An optimization for faster page loading.
    list_select_related = ('user', 'mock_test')

    # This is a custom method to display the percentage in the admin list.
    def percentage_display(self, obj):
        try:
            # Calculate the percentage.
            return f"{(obj.score / obj.max_marks) * 100:.2f}%"
        except (ValueError, TypeError, ZeroDivisionError):
            return "N/A"
    # Sets the column header for our custom method.
    percentage_display.short_description = "Percentage"


# Register the remaining models to make them visible in the admin.
admin.site.register(Subject)
admin.site.register(UserAnswer)