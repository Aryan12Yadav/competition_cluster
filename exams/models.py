# FILE: exams/models.py (Final, Verified Production Code)

from django.db import models
from django.contrib.auth import get_user_model 
from django.template.defaultfilters import slugify
from django.db.models import Sum

# Get the active User model for relationships
User = get_user_model()

# =========================================================================
# 1. ORGANIZATIONAL MODELS
# =========================================================================

class Subject(models.Model):
    """Represents a subject like 'Reasoning', 'English', etc."""
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class ExamCategory(models.Model):
    """Represents a top-level category of exams, e.g., 'SSC', 'Banking'."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, editable=False) 
    
    class Meta: 
        verbose_name_plural = "Exam Categories"
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def __str__(self): return self.name

# =========================================================================
# 2. CORE CONTENT MODELS (MockTest must come after ExamCategory)
# =========================================================================

class MockTest(models.Model):
    """Represents a single mock test, which contains multiple questions."""
    category = models.ForeignKey(ExamCategory, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200)
    
    # Flags and tracking
    is_free = models.BooleanField(default=True)
    is_new = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    attempts_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NOTE: These fields store pre-calculated or default values
    question_count = models.IntegerField()
    max_marks = models.IntegerField()
    time_minutes = models.IntegerField()

    def __str__(self): return f"{self.title} ({self.category.name})"

# Define Question first, as Option needs it.
class Question(models.Model):
    """Represents a single question within a MockTest."""
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE, related_name='questions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions', null=True)
    text = models.TextField(verbose_name="Question Text")
    
    DIFFICULTY_CHOICES = [('E', 'Easy'), ('M', 'Medium'), ('H', 'Hard')]
    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES, default='M')
    marks = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    negative_marks = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    solution = models.TextField(blank=True, null=True)
    
    # CRITICAL FIELD: Links the Question to the ONE correct Option (used for scoring and admin).
    correct_option = models.ForeignKey('Option', on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='correct_for_question', 
                                     help_text="Set the correct option after saving all options.")

    def __str__(self): return f"{self.mock_test.title}: {self.text[:50]}..."

class Option(models.Model):
    """Represents a single multiple-choice option for a Question."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500)
    # The 'is_correct' field is removed as correctness is tracked by Question.correct_option
    def __str__(self): return f"{self.question.id}: {self.text[:30]}"

# =========================================================================
# 3. USER INTERACTION & RESULT MODELS
# =========================================================================
    
class TestResult(models.Model):
    """Stores the summary results of a user's single test attempt."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results')
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE)
    
    # Scoring
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    correct_answers = models.IntegerField()
    incorrect_answers = models.IntegerField()
    unattempted = models.IntegerField()
    
    # Time Tracking
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(auto_now_add=True)
    time_taken_seconds = models.PositiveIntegerField(default=0)
    
    def __str__(self): return f"{self.user.username} - {self.mock_test.title} ({self.score})"

class UserAnswer(models.Model):
    """Stores the specific option a user selected for a question during a test attempt."""
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    
    # Crucial field added to speed up results_view aggregation
    is_correct = models.BooleanField(default=False) 
    
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent on the question in seconds")
    
    def __str__(self): return f"Answer for Q:{self.question.id} in TestResult:{self.test_result.id}"

class Testimonial(models.Model):
    """Represents a user testimonial for the homepage."""
    user_name = models.CharField(max_length=100)
    feedback_text = models.TextField()
    is_featured = models.BooleanField(default=False)
    user_avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) 
    def __str__(self): return f"Testimonial by {self.user_name}"