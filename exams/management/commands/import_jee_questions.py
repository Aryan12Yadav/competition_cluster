# FILE: exams/management/commands/import_jee_questions.py (UPDATED WITH ROBUST PARSING)

import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from exams.models import MockTest, Subject, Question, Option, ExamCategory 

# Define the maximum allowed questions per file
MAX_QUESTIONS_PER_CSV = 75 

class Command(BaseCommand):
    """
    Imports questions specifically for JEE MAINS. 
    It defaults to the 'jee-mains' ExamCategory slug.
    """
    help = f'Imports questions, and automatically creates Mock Tests, defaulting to the JEE MAINS category, with a max limit of {MAX_QUESTIONS_PER_CSV} questions.'

    def add_arguments(self, parser):
        # Mandatory argument for the path to the CSV file
        parser.add_argument('csv_file_path', type=str, help='The path to the JEE MAINS CSV file.')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        self.stdout.write(self.style.SUCCESS(f"Starting JEE MAINS import from {file_path}..."))

        # 1. Check for the specific JEE MAINS Category
        try:
            default_category = ExamCategory.objects.get(slug='jee-mains')
        except ExamCategory.DoesNotExist:
            raise CommandError("The JEE MAINS ExamCategory (slug: 'jee-mains') was not found. Please create it in the admin panel before running this command.")

        try:
            # First pass: Count the total number of rows (questions)
            with open(file_path, 'r', encoding='utf-8') as file:
                row_count = sum(1 for row in file) - 1 
                
            if row_count > MAX_QUESTIONS_PER_CSV:
                raise CommandError(f"File limit exceeded! This command can only process a maximum of {MAX_QUESTIONS_PER_CSV} questions per CSV. Found {row_count} rows.")
            
            # Second pass: Process the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                total_questions = 0
                total_marks = 0
                
                for row_num, row in enumerate(reader, 1):
                    # Use a master try-except for skipping rows gracefully
                    try:
                        # 2. Parse required fields
                        mock_test_title = row['mock_test_title']
                        subject_name = row['subject_name']
                        question_text = row['question_text']
                        solution_text = row['solution']
                        options_text = [row['option1'], row['option2'], row['option3'], row['option4']]

                        # --- ROBUST CONVERSION START ---
                        
                        # Fix 1: Safely convert Correct Option to Integer (must be 1-4)
                        correct_option_raw = row.get('correct_option', '').strip()
                        if not correct_option_raw or not correct_option_raw.isdigit():
                            raise ValueError(f"Correct option '{correct_option_raw}' is not a number (1-4).")
                        correct_option_index = int(correct_option_raw) - 1
                        if not (0 <= correct_option_index <= 3):
                            raise ValueError(f"Correct option number must be between 1 and 4.")

                        # Fix 2: Safely convert Marks/Negative Marks to Float
                        # Defaults to 4.0 and 1.0 if invalid/empty
                        marks_str = row.get('marks', '4').strip()
                        negative_marks_str = row.get('negative_marks', '1').strip()

                        marks = float(marks_str)
                        negative_marks = float(negative_marks_str)
                        
                        # --- ROBUST CONVERSION END ---

                        # 3. Get or Create MockTest (Logic remains the same)
                        mock_test, created = MockTest.objects.get_or_create(
                            title=mock_test_title,
                            defaults={
                                'category': default_category, 
                                'question_count': MAX_QUESTIONS_PER_CSV,       
                                'max_marks': MAX_QUESTIONS_PER_CSV * 4,           
                                'time_minutes': 180,        
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Row {row_num}: New MockTest '{mock_test_title}' was created automatically for JEE MAINS."))

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
                        )

                        # 6. Create Option objects
                        created_options = []
                        for text in options_text:
                            option = Option.objects.create(question=question, text=text.strip())
                            created_options.append(option)
                        
                        # 7. Set the correct_option ForeignKey on the Question
                        correct_option_instance = created_options[correct_option_index]
                        question.correct_option = correct_option_instance
                        question.save()

                        total_questions += 1
                        total_marks += marks 
                        
                        self.stdout.write(f"Row {row_num}: Successfully imported question for '{mock_test_title}'.")

                    except (KeyError, ValueError, IndexError, ObjectDoesNotExist) as e:
                        # This combined block catches missing columns, conversion failures, and invalid data
                        error_detail = str(e).splitlines()[0]
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Skipping due to data error or conversion failure: {error_detail}."))
                        continue
                
                # 8. Final Update to MockTest counts
                mock_test.question_count = total_questions
                mock_test.max_marks = int(total_marks)
                mock_test.save()

                self.stdout.write(self.style.SUCCESS('--- JEE MAINS Import Complete! ---'))

        except FileNotFoundError:
            raise CommandError(f'Error: File not found at: {file_path}')
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e} | {e.__class__.__name__}")