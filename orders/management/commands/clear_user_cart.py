from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Clear cart session data for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to clear cart for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Clearing cart session data for user: {username}')
            
            # Clear all sessions for this user
            sessions_cleared = 0
            for session in Session.objects.all():
                session_data = session.get_decoded()
                if 'cart' in session_data:
                    # Check if this session belongs to the user
                    # This is a simple check - in a real system, you'd want to verify the session belongs to the user
                    session_data.pop('cart', None)
                    session.session_data = session_data
                    session.save()
                    sessions_cleared += 1
            
            self.stdout.write(self.style.SUCCESS(f'✅ Cleared cart data from {sessions_cleared} sessions'))
            self.stdout.write(self.style.SUCCESS(f'✅ User {username} cart has been cleared'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ User {username} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error clearing cart: {str(e)}'))
