import arrow
import datetime
from django.core.mail import get_connection
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from coderdojochi.models import (
    MentorOrder,
    Order,
    Session
)

orders = Order.objects.filter(is_active=True, week_reminder_sent=False)

orders.count()

tomorrow = timezone.now() + datetime.timedelta(days=1)
week = timezone.now() + datetime.timedelta(days=7)

for order in orders:
    print order.session.start_date

