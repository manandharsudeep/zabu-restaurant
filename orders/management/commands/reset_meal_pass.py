from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orders.models import MealPassSubscription, MealPassSelection, MealPassUsage
from django.utils import timezone

class Command(BaseCommand):
    help = 'Reset meal pass for a specific user (sudeep)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to reset meal pass for (default: sudeep)',
            default='sudeep'
        )
    
    def handle(self, *args, **options):
        username = options['username']
        
        try:
            # Get the user
            user = User.objects.get(username=username)
            
            # Get all meal pass subscriptions for this user
            subscriptions = MealPassSubscription.objects.filter(user=user)
            
            if not subscriptions.exists():
                self.stdout.write(f'No meal pass subscriptions found for user "{username}"')
                return
            
            # Delete all meal pass selections
            selections = MealPassSelection.objects.filter(user=user)
            selections_deleted = selections.count()
            
            # Delete all meal pass usage records
            usage_records = MealPassUsage.objects.filter(user=user)
            usage_deleted = usage_records.count()
            
            # Delete all meal pass subscriptions
            subscriptions_deleted = subscriptions.count()
            
            self.stdout.write(f'Successfully reset meal pass for user "{username}":')
            self.stdout.write(f'  - Deleted {subscriptions_deleted} meal pass subscriptions')
            self.stdout.write(f'  - Deleted {selections_deleted} meal selections')
            self.stdout.write(f'  - Deleted {usage_deleted} usage records')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error resetting meal pass: {str(e)}'))
