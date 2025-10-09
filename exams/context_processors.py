from .models import ExamCategory

def all_categories_context(request):
    """
    Makes the list of all exam categories available to every template.
    """
    all_categories = ExamCategory.objects.all().order_by('name')
    return {
        'all_categories': all_categories
    }