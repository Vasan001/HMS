from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Appointment

class Command(BaseCommand):
    help = 'Resets the token numbers for appointments daily'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        appointments = Appointment.objects.filter(token_reset_date__lt=today)

        for appointment in appointments:
            # Ensure token_number is set to a valid value (e.g., 0 or any other number)
            appointment.token_number = 0  # Set the token number to 0 or another default value
            appointment.token_reset_date = today
            appointment.save()

        self.stdout.write(self.style.SUCCESS('Successfully reset the tokens.'))
