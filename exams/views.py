# FILE: exams/views.py (FINAL, VERIFIED PRODUCTION CODE)

# Add this import at the top of your views.py file for the login form
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
# Import essential database tools for complex queries
from django.db.models import Sum, OuterRef, Subquery, Count, Case, When, Value, IntegerField, FloatField
from django.db import transaction # Ensures database operations are atomic
from django.core.paginator import Paginator
import json

# Django Channels Imports (for real-time updates)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import MockTest, Testimonial, ExamCategory, Question, TestResult, Option, UserAnswer, Subject
from .forms import CustomUserCreationForm 

# =========================================================================
# 1. PUBLIC & AUTHENTICATION VIEWS
# =========================================================================

def home_view(request):
    """Renders the homepage and prepares login/signup forms for the popup modal."""
    all_categories = ExamCategory.objects.all().order_by('name')
    featured_test = MockTest.objects.order_by('-created_at').first()
    login_form = AuthenticationForm()
    signup_form = CustomUserCreationForm()
    context = {
        'page_title': 'Competition Cluster - Mock Tests for All Exams',
        'all_categories': all_categories,
        'featured_test': featured_test,
        'login_form': login_form,
        'signup_form': signup_form,
    }
    # Provide code with comments: This view is the entry point, rendering the modal
    return render(request, 'exams/home.html', context)

def signup_view(request):
    """Handles new user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = CustomUserCreationForm()
    context = {'form': form, 'page_title': 'User Registration'}
    # Provide code with comments: Renders the custom signup form
    return render(request, 'exams/signup.html', context)

def search_view(request):
    """Handles the search query from the navbar."""
    query = request.GET.get('q', '')
    if query:
        # Provide code with comments: Performs case-insensitive title search
        results = MockTest.objects.filter(title__icontains=query)
    else:
        results = []
    context = {
        'page_title': f"Search Results for '{query}'",
        'query': query,
        'results': results,
    }
    # Provide code with comments: Searches tests by title and displays results
    return render(request, 'exams/search_results.html', context)

def category_detail_view(request, category_slug):
    """Displays the detail page for a single category."""
    category = get_object_or_404(ExamCategory, slug=category_slug)
    # Provide code with comments: Fetches the most recent test in the category
    featured_test = MockTest.objects.filter(category=category).order_by('-created_at').first()
    context = {
        'page_title': f"{category.name} Test Series",
        'category': category,
        'featured_test': featured_test,
    }
    # Provide code with comments: Loads category details and a featured test
    return render(request, 'exams/category_detail.html', context)

def test_list_view(request, category_slug):
    """Displays a paginated list of all mock tests for a specific category."""
    category = get_object_or_404(ExamCategory, slug=category_slug)
    all_tests_list = MockTest.objects.filter(category=category).order_by('-created_at')

    if request.user.is_authenticated:
        # Provide code with comments: Subquery to check if the user has completed the test (for 'Result' button display)
        user_results_subquery = TestResult.objects.filter(
            mock_test=OuterRef('pk'), user=request.user
        ).order_by('-end_time').values('pk')[:1]
        all_tests_list = all_tests_list.annotate(user_result_id=Subquery(user_results_subquery))

    paginator = Paginator(all_tests_list, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_title': f'{category.name} Mock Tests',
        'category': category,
        'page_obj': page_obj,
    }
    # Provide code with comments: Renders the list with pagination
    return render(request, 'exams/test_list.html', context)

@login_required
def test_instructions_view(request, test_id):
    """Displays instructions and a subject-wise breakdown for a test."""
    mock_test = get_object_or_404(MockTest, pk=test_id)
    # Provide code with comments: Aggregates question counts and total marks by subject
    subject_breakdown = Question.objects.filter(mock_test=mock_test) \
                                        .values('subject__name') \
                                        .annotate(question_count=Count('id'), total_marks=Sum('marks')) \
                                        .order_by('subject__name')
    context = {
        'page_title': f"Instructions for {mock_test.title}",
        'mock_test': mock_test,
        'subject_breakdown': subject_breakdown,
    }
    # Provide code with comments: Renders test instructions
    return render(request, 'exams/test_instructions.html', context)

@login_required 
def start_test_view(request, test_id):
    """Renders the live test interface."""
    # Provide code with comments: Prefetches options for performance
    mock_test = get_object_or_404(MockTest.objects.prefetch_related('questions__options'), pk=test_id)
    questions = mock_test.questions.all()
    context = {
        'page_title': f'Live Test: {mock_test.title}', 
        'mock_test': mock_test, 
        'questions': questions
    }
    # Provide code with comments: Loads questions and options for the live test page
    return render(request, 'exams/live_test.html', context)


# =========================================================================
# 2. CORE LOGIC VIEWS (FINAL FIXED SCORING LOGIC)
# =========================================================================

@login_required
@transaction.atomic
def submit_test_view(request, test_id):
    """
    Receives test answers via POST, grades the test, and saves all results.
    FINAL FIX: Gracefully handles None/null values and ensures INT comparison, resolving the crash.
    """
    if request.method != 'POST': 
        return HttpResponseBadRequest("Invalid request method.")
    
    try:
        data = json.loads(request.body)
        user_answers_data = data.get('answers', [])
        
        mock_test = get_object_or_404(MockTest, pk=test_id)
        
        # Provide code with comments: Fetch questions and max marks efficiently
        questions_with_correct_option = Question.objects.filter(mock_test=mock_test) \
            .select_related('correct_option')
        
        total_correct, total_incorrect, final_score = 0, 0, 0
        total_time_taken = 0
        total_max_marks = questions_with_correct_option.aggregate(Sum('marks'))['marks__sum'] or 0
        
        # Provide code with comments: Build map using INTEGER keys for safe comparison
        correct_answers_map = {}
        for q in questions_with_correct_option:
            # Provide code with comments: Ensure marks/negative_marks are floats for safe arithmetic
            marks = float(q.marks if q.marks is not None else 0)
            negative_marks = float(q.negative_marks if q.negative_marks is not None else 0)

            correct_answers_map[int(q.id)] = { # Key is INT
                'correct_option_id': q.correct_option_id, # Value is INT or None
                'marks': marks,
                'negative_marks': negative_marks
            }

        answered_q_ids = set()
        answers_to_create = []
        
        for answer_data in user_answers_data:
            q_id = int(answer_data.get('question_id')) # Convert incoming string Q_ID to INT
            time_spent = answer_data.get('time_spent', 0)
            
            # --- CRITICAL CRASH FIX: Safely parse selected option ID ---
            selected_id_raw = answer_data.get('selected_option_id')
            
            if selected_id_raw is None or str(selected_id_raw).lower() == 'null' or str(selected_id_raw) == '':
                selected_option_id = None # Set to Python None if unattempted
            else:
                # Convert the selected ID to an integer for safe comparison
                selected_option_id = int(selected_id_raw) 
            # --- CRITICAL CRASH FIX END ---

            total_time_taken += time_spent
            is_correct = False
            
            if selected_option_id is not None: 
                # Provide code with comments: Only proceed with scoring if an answer was selected
                answered_q_ids.add(q_id)
                
                if q_id in correct_answers_map:
                    q_data = correct_answers_map[q_id]
                    
                    # Provide code with comments: Scoring Logic with explicit check for None in DB data
                    if q_data['correct_option_id'] is not None and selected_option_id == q_data['correct_option_id']:
                        is_correct = True
                        total_correct += 1
                        final_score += q_data['marks']
                    else:
                        total_incorrect += 1
                        final_score -= q_data['negative_marks']
            
            # Provide code with comments: Prepare UserAnswer for bulk creation
            answers_to_create.append(UserAnswer(
                test_result=None, 
                question_id=q_id, 
                selected_option_id=selected_option_id,
                time_spent=time_spent,
                is_correct=is_correct 
            ))
        
        total_unattempted = questions_with_correct_option.count() - len(answered_q_ids)
        final_score = max(0, final_score)

        # Provide code with comments: Create the main TestResult record
        result = TestResult.objects.create(
            user=request.user, mock_test=mock_test, score=final_score,
            max_marks=total_max_marks, correct_answers=total_correct,
            incorrect_answers=total_incorrect, unattempted=total_unattempted,
            start_time=timezone.now(), 
            end_time=timezone.now(),
            time_taken_seconds=total_time_taken,
        )
        
        # Provide code with comments: Bulk create UserAnswer objects
        for answer in answers_to_create:
            answer.test_result = result
        UserAnswer.objects.bulk_create(answers_to_create)
        
        # Provide code with comments: Channels Integration (Real-time update broadcast)
        channel_layer = get_channel_layer()
        leaderboard_data = list(
            TestResult.objects.filter(mock_test=mock_test)
            .order_by('-score', 'time_taken_seconds')[:10]
            .values('user__username', 'score', 'time_taken_seconds')
        )
        
        final_leaderboard = []
        for i, res in enumerate(leaderboard_data):
            final_leaderboard.append({
                'rank': i + 1,
                'username': res['user__username'],
                'score': float(res['score']),
                'time_taken_seconds': res['time_taken_seconds']
            })

        async_to_sync(channel_layer.group_send)(
            'leaderboard',  
            {'type': 'leaderboard_update', 'text': json.dumps(final_leaderboard)}
        )

        # Provide code with comments: Success response for frontend redirection to results page
        return JsonResponse({'status': 'success', 'result_id': result.id})

    except Exception as e:
        # Provide code with comments: Logs error details and returns a generic 500 error to the client
        print(f"ERROR in submit_test_view: {e}")
        return JsonResponse({'status': 'error', 'message': "An internal error occurred during scoring."}, status=500)


# =========================================================================
# 3. OTHER VIEWS (Fixed for consistency)
# =========================================================================

@login_required
def results_view(request, result_id):
    """Displays an advanced analysis of a user's test result."""
    result = get_object_or_404(TestResult, pk=result_id, user=request.user)
    user_answers = result.user_answers.select_related('question', 'selected_option')
    
    # Provide code with comments: Aggregate time spent on correct/incorrect answers
    time_stats = user_answers.aggregate(
        total_time_spent=Sum('time_spent'),
        time_on_correct=Sum(Case(When(is_correct=True, then='time_spent'), default=Value(0), output_field=IntegerField())),
        time_on_incorrect=Sum(Case(When(is_correct=False, selected_option__isnull=False, then='time_spent'), default=Value(0), output_field=IntegerField()))
    )
    
    # Provide code with comments: Calculate average times (avoiding division by zero)
    time_stats['time_on_correct_avg'] = time_stats['time_on_correct'] / (result.correct_answers or 1)
    time_stats['time_on_incorrect_avg'] = time_stats['time_on_incorrect'] / (result.incorrect_answers or 1)
    
    # Provide code with comments: Aggregate analysis by subject
    subject_analysis = user_answers.filter(question__subject__isnull=False) \
                                   .values('question__subject__name') \
                                   .annotate(
                                        total_in_subject=Count('id'),
                                        correct_in_subject=Count(Case(When(is_correct=True, then=1))),
                                        incorrect_in_subject=Count(Case(When(is_correct=False, selected_option__isnull=False, then=1))),
                                   ).order_by('question__subject__name')
    
    try:
        percentage = (result.score / result.max_marks) * 100 if result.max_marks > 0 else 0
    except (TypeError, ZeroDivisionError):
        percentage = 0.0

    context = {
        'page_title': f'Analysis for {result.mock_test.title}',
        'result': result,
        'percentage': round(percentage, 2),
        'time_stats': time_stats,
        'subject_analysis': subject_analysis,
    }
    # Provide code with comments: Renders the detailed results page
    return render(request, 'exams/results.html', context)

@login_required
def answer_review_view(request, result_id):
    """Displays a question-by-question review of a completed test."""
    result = get_object_or_404(TestResult, pk=result_id, user=request.user)
    
    # Provide code with comments: Fetch questions, options, and correct answer link efficiently
    all_questions = Question.objects.filter(mock_test=result.mock_test) \
        .prefetch_related('options').select_related('correct_option')
        
    user_answers = UserAnswer.objects.filter(test_result=result)
    user_answers_map = {answer.question_id: answer.selected_option_id for answer in user_answers}
    
    review_data = []
    
    for question in all_questions:
        # Provide code with comments: Fetches the correct option ID directly from the question
        correct_option_id = question.correct_option_id
        
        review_data.append({
            'question_text': question.text,
            'options': question.options.all(),
            'user_selected_option_id': user_answers_map.get(question.id),
            'correct_option_id': correct_option_id,
            'solution': question.solution,
        })
    context = {'page_title': f"Review for {result.mock_test.title}",'result': result, 'review_data': review_data}
    # Provide code with comments: Renders the answer review page
    return render(request, 'exams/answer_review.html', context)


@login_required
def leaderboard_view(request, test_id):
    """Fetches and displays the top scores for a specific mock test."""
    mock_test = get_object_or_404(MockTest, pk=test_id)
    
    # Provide code with comments: Fetches top 10 results for the leaderboard
    top_scores = TestResult.objects.filter(mock_test=mock_test).order_by('-score', 'time_taken_seconds')[:10]
    
    context = {
        'page_title': f"Leaderboard for {mock_test.title}",
        'mock_test': mock_test,
        'top_scores': top_scores,
    }
    # Provide code with comments: Renders the leaderboard page (real-time data fetched via WebSocket)
    return render(request, 'exams/leaderboard.html', context)


@login_required 
def dashboard_view(request):
    """Renders the personalized user dashboard."""
    user_results = TestResult.objects.filter(user=request.user).order_by('-end_time')
    tests_completed_count = user_results.values('mock_test').distinct().count()
    context = {
        'page_title': f'{request.user.username}\'s Dashboard',
        'last_login': request.user.last_login,
        'tests_completed_count': tests_completed_count,
        'test_results': user_results,
    }
    # Provide code with comments: Renders the user dashboard with key stats
    return render(request, 'exams/dashboard.html', context)

@login_required
def category_dashboard_view(request):
    """Demonstrates using a subquery to annotate each category."""
    # Provide code with comments: Uses Subquery to find the latest test title for each category
    latest_tests = MockTest.objects.filter(category=OuterRef('pk')).order_by('-created_at')
    categories = ExamCategory.objects.annotate(latest_test_title=Subquery(latest_tests.values('title')[:1]))
    context = {'page_title': "Category Dashboard", 'categories_with_latest_test': categories}
    # Provide code with comments: Renders the category overview dashboard
    return render(request, 'exams/category_dashboard.html', context)