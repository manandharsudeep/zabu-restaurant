from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from orders.models import Category, MenuItem
import os

class Command(BaseCommand):
    help = 'Create sample menu items with placeholder images'
    
    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {'name': 'Appetizers', 'description': 'Start your meal with our delicious appetizers'},
            {'name': 'Main Courses', 'description': 'Hearty main courses to satisfy your hunger'},
            {'name': 'Desserts', 'description': 'Sweet endings to complete your meal'},
            {'name': 'Beverages', 'description': 'Refreshing drinks to complement your meal'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            print(f"Category: {category.name} - {'Created' if created else 'Already exists'}")
        
        # Create menu items
        menu_items_data = [
            {
                'category': 'Appetizers',
                'name': 'Chicken Tikka',
                'description': 'Tender chicken marinated in yogurt and spices, grilled to perfection',
                'price': '350.00',
                'preparation_time': 20,
                'available': True,
            },
            {
                'category': 'Appetizers',
                'name': 'Vegetable Spring Rolls',
                'description': 'Fresh vegetables wrapped in spring roll pastry, served with sweet chili sauce',
                'price': '180.00',
                'preparation_time': 15,
                'available': True,
            },
            {
                'category': 'Main Courses',
                'name': 'Mutton Curry',
                'description': 'Tender mutton cooked in aromatic spices and herbs',
                'price': '450.00',
                'preparation_time': 30,
                'available': True,
            },
            {
                'category': 'Main Courses',
                'name': 'Chicken Biryani',
                'description': 'Fragrant basmati rice cooked with tender chicken and aromatic spices',
                'price': '380.00',
                'preparation_time': 25,
                'available': True,
            },
            {
                'category': 'Desserts',
                'name': 'Gulab Jamun',
                'description': 'Soft and spongy milk solids soaked in sugar syrup',
                'price': '120.00',
                'preparation_time': 10,
                'available': True,
            },
            {
                'category': 'Desserts',
                'name': 'Rasmalai',
                'description': 'Delicate Indian cheese balls soaked in sugar syrup',
                'price': '150.00',
                'preparation_time': 5,
                'available': True,
            },
            {
                'category': 'Beverages',
                'name': 'Mango Lassi',
                'description': 'Sweet and creamy mango yogurt drink',
                'price': '80.00',
                'preparation_time': 5,
                'available': True,
            },
            {
                'category': 'Beverages',
                'name': 'Masala Tea',
                'description': 'Traditional spiced tea with milk and sugar',
                'price': '60.00',
                'preparation_time': 5,
                'available': True,
            },
        ]
        
        for item_data in menu_items_data:
            category = Category.objects.get(name=item_data['category'])
            menu_item, created = MenuItem.objects.get_or_create(
                category=category,
                name=item_data['name'],
                defaults={
                    'description': item_data['description'],
                    'price': item_data['price'],
                    'preparation_time': item_data['preparation_time'],
                    'available': item_data['available'],
                }
            )
            print(f"Menu Item: {menu_item.name} - {'Created' if created else 'Already exists'}")
        
        print("Sample menu items created successfully!")
