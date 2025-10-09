# FILE: exams/management/commands/import_questions.py (FINAL CORRECTED VERSION)

import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# Import all necessary models
from exams.models import ExamCategory, MockTest, Subject, Question, Option 
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Imports questions from a CSV. Automatically creates Mock Tests if they do not exist.'

    def add_arguments(self, parser):
        # Changed argument name to match the error output context (cgl_pre_mock2.csv)
        parser.add_argument('csv_file_path', type=str, help='The path to the CSV file.')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        self.stdout.write(self.style.SUCCESS(f"Starting smart import from {file_path}..."))

        # 1. Check for Default Category
        try:
            default_category = ExamCategory.objects.get(slug='ssc-cgl')
        except ExamCategory.DoesNotExist:
            raise CommandError("A default ExamCategory with slug 'ssc-cgl' was not found. Please create it in the admin panel before running this command.")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Lists to hold newly created options and questions for setting Foreign Keys later
                questions_to_update = []
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # 2. Parse required fields
                        mock_test_title = row['mock_test_title']
                        subject_name = row['subject_name']
                        question_text = row['question_text']
                        solution_text = row['solution']
                        marks = float(row['marks'])
                        negative_marks = float(row['negative_marks'])
                        options_text = [row['option1'], row['option2'], row['option3'], row['option4']]
                        correct_option_index = int(row['correct_option']) - 1 # 1-based index to 0-based

                        # 3. Get or Create MockTest
                        mock_test, created = MockTest.objects.get_or_create(
                            title=mock_test_title,
                            defaults={
                                'category': default_category,
                                'question_count': 100,
                                'max_marks': 200,
                                'time_minutes': 60,
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Row {row_num}: New MockTest '{mock_test_title}' was created automatically."))

                        # 4. Get or Create Subject
                        subject, _ = Subject.objects.get_or_create(name=subject_name)
                        
                        # 5. Create the Question object
                        question = Question.objects.create(
                            mock_test=mock_test,
                            subject=subject,
                            text=question_text,
                            solution=solution_text,
                            marks=marks,
                            negative_marks=negative_marks,
                            # correct_option is still NULL at this point
                        )

                        # 6. Create Option objects (FIX: Removed is_correct argument)
                        created_options = []
                        for text in options_text:
                            # We must create the options first to get their primary keys
                            option = Option.objects.create(question=question, text=text.strip())
                            created_options.append(option)
                        
                        # 7. Set the correct_option ForeignKey on the Question
                        correct_option_instance = created_options[correct_option_index]
                        question.correct_option = correct_option_instance
                        question.save() # Save the question with the correct foreign key

                        self.stdout.write(f"Row {row_num}: Successfully imported question for '{mock_test_title}'.")

                    except (KeyError, ValueError, IndexError) as e:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Skipping due to data error: {e}."))
                        continue
                
                # NOTE: You may want to add logic here to update the final question_count/max_marks on the MockTest object(s)

        except FileNotFoundError:
            raise CommandError(f'File not found at: {file_path}')
        except Exception as e:
            # FIX: Catch general exceptions and report, preventing silent failures
            raise CommandError(f"An unexpected error occurred: {e}")