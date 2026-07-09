import time

from django.core.management.base import BaseCommand

from task.producer import producer


class Command(BaseCommand):
    help = (
        "DLQ recovery worker: republishes pending Dead Letter Queue entries to "
        "their original Kafka topics once the broker is reachable again."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=float,
            default=5,
            help='Seconds to wait between polling passes (default: 5).',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Process one batch of pending entries and exit (useful for a cron job).',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS('DLQ recovery worker starting...'))

        while True:
            processed = producer.reprocess_pending_dlq_entries()
            if processed:
                self.stdout.write(self.style.SUCCESS(f'Republished {processed} DLQ entr{"y" if processed == 1 else "ies"}'))

            if run_once:
                break
            time.sleep(interval)
