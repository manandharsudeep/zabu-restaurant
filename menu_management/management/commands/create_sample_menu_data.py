from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from menu_management.models import Menu, MenuSection, RecipeMenuItem, Ingredient, Recipe, RecipeIngredient
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Create sample menu data for digital menu API testing'

    def handle(self, *args, **options):
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        # Create sample ingredients
        ingredients_data = [
            ('Ground Beef', 'kg', Decimal('8.50')),
            ('Burger Buns', 'pcs', Decimal('0.80')),
            ('Lettuce', 'kg', Decimal('3.20')),
            ('Tomato', 'kg', Decimal('4.10')),
            ('Cheese', 'kg', Decimal('12.50')),
            ('Pizza Dough', 'kg', Decimal('2.30')),
            ('Mozzarella', 'kg', Decimal('8.90')),
            ('Pizza Sauce', 'l', Decimal('4.50')),
            ('Pasta', 'kg', Decimal('3.80')),
            ('Chicken Breast', 'kg', Decimal('11.20')),
        ]
        
        ingredients = []
        for name, unit, price in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(
                name=name,
                defaults={
                    'unit': unit,
                    'current_price': price,
                    'description': f'Fresh {name} for restaurant use',
                }
            )
            ingredients.append(ingredient)
        
        # Create sample recipes
        recipes_data = [
            ('Classic Burger', 'Juicy beef patty with fresh vegetables', 15),
            ('Margherita Pizza', 'Classic Italian pizza with mozzarella and basil', 20),
            ('Spaghetti Carbonara', 'Creamy pasta with bacon and parmesan', 18),
            ('Grilled Chicken', 'Tender grilled chicken breast with herbs', 22),
            ('Caesar Salad', 'Fresh romaine lettuce with caesar dressing', 12),
        ]
        
        recipes = []
        for name, description, prep_time in recipes_data:
            recipe, created = Recipe.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'prep_time': prep_time,
                    'cook_time': prep_time + 5,
                    'total_time': prep_time + 10,
                    'difficulty': 2,
                    'portions': 1,
                    'cost_per_portion': Decimal('5.00'),
                    'selling_price': Decimal('15.00'),
                    'chef_notes': f'Best {name} in town!',
                    'created_by': admin_user,
                }
            )
            recipes.append(recipe)
        
        # Add ingredients to recipes
        recipe_ingredients_map = {
            recipes[0]: [ingredients[0], ingredients[1], ingredients[2], ingredients[3], ingredients[4]],  # Burger
            recipes[1]: [ingredients[5], ingredients[6], ingredients[7]],  # Pizza
            recipes[2]: [ingredients[8], ingredients[9]],  # Pasta
            recipes[3]: [ingredients[9]],  # Chicken
            recipes[4]: [ingredients[2], ingredients[3]],  # Salad
        }
        
        for recipe, ing_list in recipe_ingredients_map.items():
            for ingredient in ing_list:
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    defaults={
                        'quantity': Decimal(str(random.uniform(0.1, 2.0))),
                        'unit': ingredient.unit,
                    }
                )
        
        # Get existing menu and section
        menu = Menu.objects.first()
        if not menu:
            menu = Menu.objects.create(
                name='Main Menu',
                description='Our delicious menu',
                created_by=admin_user,
            )
        
        menu_section = MenuSection.objects.first()
        if not menu_section:
            menu_section = MenuSection.objects.create(
                menu=menu,
                name='Main Courses',
                description='Our main dishes',
                order=1,
            )
        
        # Create RecipeMenuItem objects
        menu_items_data = [
            (recipes[0], 'Classic Burger', 'Our signature beef burger with fresh lettuce, tomato, and cheese', Decimal('12.99')),
            (recipes[1], 'Margherita Pizza', 'Traditional Italian pizza with fresh mozzarella and basil', Decimal('14.99')),
            (recipes[2], 'Spaghetti Carbonara', 'Creamy pasta with crispy bacon and parmesan cheese', Decimal('13.99')),
            (recipes[3], 'Grilled Chicken Breast', 'Tender grilled chicken with herbs and vegetables', Decimal('16.99')),
            (recipes[4], 'Caesar Salad', 'Fresh romaine lettuce with caesar dressing and croutons', Decimal('9.99')),
        ]
        
        for recipe, name, description, price in menu_items_data:
            menu_item, created = RecipeMenuItem.objects.get_or_create(
                name=name,
                defaults={
                    'menu_section': menu_section,
                    'recipe': recipe,
                    'description': description,
                    'price': price,
                    'is_available': True,
                    'order': random.randint(1, 100),
                    'dietary_info': {'vegetarian': False, 'vegan': False, 'gluten_free': False},
                    'prep_time': recipe.prep_time,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Sample menu data created successfully!'))
        self.stdout.write(f'Created {RecipeMenuItem.objects.count()} menu items')
