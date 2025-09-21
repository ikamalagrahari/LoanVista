from django.core.management.base import BaseCommand
from loans.tasks import ingest_customer_data, ingest_loan_data


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def handle(self, *args, **options):
        ingest_customer_data.delay()
        ingest_loan_data.delay()
        self.stdout.write(self.style.SUCCESS('Data ingestion tasks queued.'))