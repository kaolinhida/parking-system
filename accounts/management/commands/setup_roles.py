from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.permissions import GATE_OPERATOR_GROUP, PARKING_ADMIN_GROUP


class Command(BaseCommand):
    help = 'Create staff role groups for the parking system.'

    def handle(self, *args, **options):
        for group_name in (PARKING_ADMIN_GROUP, GATE_OPERATOR_GROUP):
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group.name}'))
            else:
                self.stdout.write(f'Group already exists: {group.name}')
