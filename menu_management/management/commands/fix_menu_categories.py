from django.core.management.base import BaseCommand
from menu_management.models import MenuSection, RecipeMenuItem, Menu
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Fix menu categories and create proper menu sections'

    def handle(self, *args, **options):
        # Get the main menu
        menu = Menu.objects.first()
        if not menu:
            self.stdout.write(self.style.ERROR('No menu found!'))
            return
        
        # Create proper menu sections
        sections_data = [
            ('Appetizers', 'Start your meal with our delicious appetizers'),
            ('Main Courses', 'Hearty main dishes for the hungry diner'),
            ('Pasta & Pizza', 'Italian favorites and specialty pizzas'),
            ('Salads & Light', 'Fresh and healthy options'),
            ('Desserts', 'Sweet endings to your meal'),
            ('Beverages', 'Refreshing drinks and beverages'),
        ]
        
        sections = {}
        for name, description in sections_data:
            section, created = MenuSection.objects.get_or_create(
                menu=menu,
                name=name,
                defaults={
                    'description': description,
                    'order': len(sections) + 1,
                }
            )
            sections[name] = section
        
        # Update menu items with correct categories
        item_categories = {
            'Caesar Salad': 'Salads & Light',
            'Classic Burger': 'Main Courses', 
            'Grilled Chicken Breast': 'Main Courses',
            'Margherita Pizza': 'Pasta & Pizza',
            'Spaghetti Carbonara': 'Pasta & Pizza',
        }
        
        updated_count = 0
        for item_name, category_name in item_categories.items():
            try:
                item = RecipeMenuItem.objects.get(name=item_name)
                item.menu_section = sections[category_name]
                item.save()
                updated_count += 1
                self.stdout.write(f'Updated: {item_name} -> {category_name}')
            except RecipeMenuItem.DoesNotExist:
                self.stdout.write(f'Item not found: {item_name}')
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} menu items with correct categories!'))
        
        # Show final result
        self.stdout.write('\n=== FINAL MENU STRUCTURE ===')
        for section_name, section in sections.items():
            items = RecipeMenuItem.objects.filter(menu_section=section)
            self.stdout.write(f'\n{section_name}:')
            for item in items:
                self.stdout.write(f'  - {item.name} (${item.price})')
