from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = "Clears the django dev server's cache"
    def handle(self, *args, **options):
        cache.clear()
        self.stdout.write('Cleared cache\n')
