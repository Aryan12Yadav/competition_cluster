# FILE: exams/management/commands/import_neet_questions.py (FINAL UPDATED NEET SPECIFICATIONS)

import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from exams.models import MockTest, Subject, Question, Option, ExamCategory 
from typing import TextIO # For safer file reading

# Define the maximum allowed questions per file
MAX_QUESTIONS_PER_CSV = 180 # <-- UPDATED: 180 Questions Limit

class Command(BaseCommand):
    """
    Imports questions specifically for NEET. 
    It defaults to the 'neet' ExamCategory slug.
    """
    help = f'Imports questions, and automatically creates Mock Tests, defaulting to the NEET category, with a max limit of {MAX_QUESTIONS_PER_CSV} questions.'

    def add_arguments(self, parser):
        # Mandatory argument for the path to the CSV file
        parser.add_argument('csv_file_path', type=str, help='The path to the NEET CSV file.')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        self.stdout.write(self.style.SUCCESS(f"Starting NEET import from {file_path}..."))

        # 1. Check for the specific NEET Category
        try:
            # Provide code with comments: This command is hardcoded to look for 'neet'
            default_category = ExamCategory.objects.get(slug='neet')
        except ExamCategory.DoesNotExist:
            raise CommandError("The NEET ExamCategory (slug: 'neet') was not found. Please create it in the admin panel before running this command.")

        try:
            # First pass: Count the total number of rows (questions)
            with open(file_path, 'r', encoding='utf-8') as file:
                # Provide code with comments: Count rows excluding the header
                row_count = sum(1 for row in file) - 1 
                
            if row_count > MAX_QUESTIONS_PER_CSV:
                raise CommandError(f"File limit exceeded! This command can only process a maximum of {MAX_QUESTIONS_PER_CSV} questions per CSV. Found {row_count} rows.")
            
            # Second pass: Process the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                total_questions = 0
                total_marks = 0
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # 2. Parse required fields (with safety checks for empty marks)
                        mock_test_title = row['mock_test_title']
                        subject_name = row['subject_name']
                        question_text = row['question_text']
                        solution_text = row['solution']
                        options_text = [row['option1'], row['option2'], row['option3'], row['option4']]
                        correct_option_index = int(row['correct_option']) - 1 # 1-based index to 0-based
                        
                        # --- ENFORCING MARKS AND NEGATIVE MARKS (FIX) ---
                        # Provide code with comments: Read from CSV, but default to 4.0 if empty/invalid
                        marks_str = row.get('marks', '4').strip()
                        negative_marks_str = row.get('negative_marks', '1').strip()
                        
                        # Provide code with comments: Safely convert to float, using 4.0 and 1.0 as defaults
                        marks = float(marks_str) if marks_str else 4.0
                        negative_marks = float(negative_marks_str) if negative_marks_str else 1.0
                        # --- END ENFORCING MARKS FIX ---

                        # 3. Get or Create MockTest (UPDATED DEFAULTS)
                        mock_test, created = MockTest.objects.get_or_create(
                            title=mock_test_title,
                            defaults={
                                'category': default_category, # Links to NEET
                                'question_count': MAX_QUESTIONS_PER_CSV, # Default Question Count
                                'max_marks': MAX_QUESTIONS_PER_CSV * 4,       # Max Marks: 180 * 4 = 720
                                'time_minutes': 180,        # 180 Minutes
                            }
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Row {row_num}: New MockTest '{mock_test_title}' was created automatically for NEET."))

                        # 4. Get or Create Subject
                        subject, _ = Subject.objects.get_or_create(name=subject_name)
                        
                        # 5. Create the Question object
                        question = Question.objects.create(
                            mock_test=mock_test,
                            subject=subject,
                            text=question_text,
                            solution=solution_text,
                            # Use the safely parsed and enforced marks/negative_marks
                            marks=marks, 
                            negative_marks=negative_marks,
                        )

                        # 6. Create Option objects
                        created_options = []
                        for text in options_text:
                            option = Option.objects.create(question=question, text=text.strip())
                            created_options.append(option)
                        
                        # 7. Set the correct_option ForeignKey on the Question (Critical for scoring)
                        correct_option_instance = created_options[correct_option_index]
                        question.correct_option = correct_option_instance
                        question.save()

                        total_questions += 1
                        total_marks += marks 
                        
                        self.stdout.write(f"Row {row_num}: Successfully imported question for '{mock_test_title}'.")

                    except (KeyError, ValueError, IndexError) as e:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Skipping due to data error or column mismatch: {e}."))
                        continue
                
                # 8. Final Update to MockTest counts
                mock_test.question_count = total_questions
                mock_test.max_marks = int(total_marks)
                mock_test.save()

                self.stdout.write(self.style.SUCCESS('--- NEET Import Complete! ---'))

        except FileNotFoundError:
            raise CommandError(f'Error: File not found at: {file_path}')
        except Exception as e:
            raise CommandError(f"An unexpected error occurred: {e} | {e.__class__.__name__}")