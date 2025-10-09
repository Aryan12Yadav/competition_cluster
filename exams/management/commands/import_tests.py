# FILE: exams/management/commands/import_tests.py (New File)

import csv
from django.core.management.base import BaseCommand
from exams.models import MockTest, ExamCategory
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Imports Mock Tests from a specified CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The path to the Mock Test CSV file.')

    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        self.stdout.write(self.style.SUCCESS(f"Starting mock test import from {file_path}..."))

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Use DictReader to read CSV rows as dictionaries
                reader = csv.DictReader(file)
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Find the parent ExamCategory using the slug from the CSV
                        category = ExamCategory.objects.get(slug=row['category_slug'])

                        # Use update_or_create to avoid creating duplicate tests.
                        # It will find a test with the same title or create a new one.
                        test, created = MockTest.objects.update_or_create(
                            title=row['title'],
                            defaults={
                                'category': category,
                                'question_count': int(row['question_count']),
                                'max_marks': int(row['max_marks']),
                                'time_minutes': int(row['time_minutes']),
                                # Handle boolean values (TRUE/FALSE) from CSV, ignoring case and whitespace
                                'is_free': row['is_free'].strip().upper() == 'TRUE',
                                'is_new': row['is_new'].strip().upper() == 'TRUE',
                                'is_popular': row['is_popular'].strip().upper() == 'TRUE',
                            }
                        )

                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Row {row_num}: Created new test '{test.title}'"))
                        else:
                            self.stdout.write(f"Row {row_num}: Updated existing test '{test.title}'")

                    except ObjectDoesNotExist:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Category with slug '{row['category_slug']}' not found. Skipping."))
                        continue
                    except KeyError as e:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Missing column in CSV: {e}. Skipping."))
                        continue
                    except ValueError as e:
                        self.stderr.write(self.style.ERROR(f"Row {row_num}: Invalid number in a column like 'question_count'. Error: {e}. Skipping."))
                        continue

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Error: File not found at '{file_path}'"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))