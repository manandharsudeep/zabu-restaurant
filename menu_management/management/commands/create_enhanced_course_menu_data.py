from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, time, datetime, timedelta
import uuid

from menu_management.enhanced_course_menu_models import (
    CourseMenuTemplate, CourseMenuInstance, CourseDefinition, 
    CourseInstance, WinePairing, BeveragePairing, CourseMenuPricing
)

class Command(BaseCommand):
    help = 'Create sample data for enhanced course menu management'

    def handle(self, *args, **options):
        self.stdout.write('Creating enhanced course menu management sample data...')
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@zabu.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        # Create sample course menu templates
        self.create_tasting_menu_template()
        self.create_prix_fixe_template()
        self.create_vegetarian_template()
        self.create_seasonal_template()
        
        # Create sample instances and pairings
        self.create_sample_instances()
        
        self.stdout.write(self.style.SUCCESS('Enhanced course menu management sample data created successfully!'))

    def create_tasting_menu_template(self):
        """Create a 7-course tasting menu template"""
        template = CourseMenuTemplate.objects.create(
            name="Signature Tasting Experience",
            description="A comprehensive 7-course journey through our chef's finest creations",
            course_count=7,
            menu_type='tasting',
            base_price=Decimal('150.00'),
            price_per_person=Decimal('185.00'),
            min_party_size=2,
            max_party_size=8,
            advance_booking_days=2,
            vegetarian_available=True,
            vegan_available=False,
            gluten_free_available=True,
            wine_pairing_available=True,
            beverage_pairing_available=True,
            sommelier_required=True,
            is_seasonal=False,
            chef_table_exclusive=False,
            required_chef_level='executive_chef',
            chef_notes="This menu showcases our seasonal ingredients and culinary techniques. Each course is designed to complement the next.",
            estimated_duration=180,
            pacing_interval=20,
            is_active=True,
        )
        
        # Create pricing tiers
        CourseMenuPricing.objects.create(
            template=template,
            tier_name='Standard',
            tier_description='Standard tasting menu experience',
            price_per_person=Decimal('185.00'),
            minimum_surcharge=Decimal('370.00'),
            min_party_size=2,
            max_party_size=4,
            ingredient_quality_multiplier=Decimal('1.0'),
            chef_level_multiplier=Decimal('1.0'),
            seasonal_multiplier=Decimal('1.0'),
            is_active=True,
        )
        
        CourseMenuPricing.objects.create(
            template=template,
            tier_name='Premium',
            tier_description='Premium ingredients and wine pairings',
            price_per_person=Decimal('250.00'),
            minimum_surcharge=Decimal('500.00'),
            min_party_size=2,
            max_party_size=6,
            ingredient_quality_multiplier=Decimal('1.5'),
            chef_level_multiplier=Decimal('1.2'),
            seasonal_multiplier=Decimal('1.0'),
            is_active=True,
        )
        
        # Create courses
        courses_data = [
            {
                'course_number': 1,
                'course_name': 'Amuse-Bouche',
                'description': 'A single bite to awaken the palate with seasonal flavors',
                'chef_notes': 'Change weekly based on seasonal availability',
                'prep_time': 5,
                'plating_time': 2,
                'presentation_time': 1,
                'main_ingredients': ['seasonal vegetables', 'microgreens', 'edible flowers'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': [],
                'wine_pairing_notes': 'Light, crisp white wine to cleanse the palate',
                'beverage_pairing_notes': 'Sparkling water with citrus',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 1,
            },
            {
                'course_number': 2,
                'course_name': 'Ocean Delicacy',
                'description': 'Fresh oysters with champagne mignonette and cucumber granita',
                'chef_notes': 'Source from local waters, serve immediately',
                'prep_time': 10,
                'plating_time': 3,
                'presentation_time': 2,
                'main_ingredients': ['oysters', 'champagne', 'cucumber', 'shallots'],
                'complexity_level': 'medium',
                'is_vegetarian': False,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': ['shellfish'],
                'wine_pairing_notes': 'Champagne or dry sparkling wine',
                'beverage_pairing_notes': 'Premium sparkling water',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 2,
            },
            {
                'course_number': 3,
                'course_name': 'Garden Symphony',
                'description': 'Heirloom tomato salad with burrata and basil oil',
                'chef_notes': 'Use the ripest tomatoes, serve at room temperature',
                'prep_time': 15,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['heirloom tomatoes', 'burrata', 'basil', 'olive oil'],
                'complexity_level': 'medium',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['dairy'],
                'wine_pairing_notes': 'Light-bodied red wine like Pinot Noir',
                'beverage_pairing_notes': 'Herbal iced tea',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 3,
            },
            {
                'course_number': 4,
                'course_name': 'Ocean Treasure',
                'description': 'Pan-seared scallops with cauliflower puree and pancetta',
                'chef_notes': 'Sear scallops to golden perfection, do not overcook',
                'prep_time': 20,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['scallops', 'cauliflower', 'pancetta', 'butter'],
                'complexity_level': 'complex',
                'is_vegetarian': False,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['shellfish', 'dairy'],
                'wine_pairing_notes': 'Chardonnay with good acidity',
                'beverage_pairing_notes': 'Sparkling mineral water',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 4,
            },
            {
                'course_number': 5,
                'course_name': 'Pastoral Elegance',
                'description': 'Grilled lamb rack with rosemary jus and seasonal vegetables',
                'chef_notes': 'Medium-rare, rest before slicing',
                'prep_time': 25,
                'plating_time': 8,
                'presentation_time': 3,
                'main_ingredients': ['lamb', 'rosemary', 'seasonal vegetables', 'red wine'],
                'complexity_level': 'complex',
                'is_vegetarian': False,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': [],
                'wine_pairing_notes': 'Medium-bodied red wine like Merlot',
                'beverage_pairing_notes': 'Full-bodied red wine',
                'pairing_intensity': 'bold',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 5,
            },
            {
                'course_number': 6,
                'course_name': 'Cheese Artistry',
                'description': 'Artisanal cheese selection with seasonal fruits and nuts',
                'chef_notes': 'Serve at room temperature, pair with appropriate accompaniments',
                'prep_time': 10,
                'plating_time': 8,
                'presentation_time': 2,
                'main_ingredients': ['artisanal cheeses', 'seasonal fruits', 'nuts', 'honey'],
                'complexity_level': 'medium',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': True,
                'contains_dairy': True,
                'allergens': ['dairy', 'nuts'],
                'wine_pairing_notes': 'Dessert wine or port',
                'beverage_pairing_notes': 'Coffee or herbal tea',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 6,
            },
            {
                'course_number': 7,
                'course_name': 'Sweet Finale',
                'description': 'Chocolate soufflé with vanilla bean ice cream',
                'chef_notes': 'Bake to order, serve immediately',
                'prep_time': 20,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['chocolate', 'eggs', 'vanilla', 'cream'],
                'complexity_level': 'chef_special',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['dairy', 'eggs'],
                'wine_pairing_notes': 'Sweet dessert wine or port',
                'beverage_pairing_notes': 'Espresso or coffee',
                'pairing_intensity': 'bold',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 7,
            },
        ]
        
        for course_data in courses_data:
            CourseDefinition.objects.create(template=template, **course_data)
        
        self.stdout.write(f'Created tasting menu template: {template.name}')

    def create_prix_fixe_template(self):
        """Create a 3-course prix fixe menu template"""
        template = CourseMenuTemplate.objects.create(
            name="Classic Prix Fixe Dinner",
            description="Three-course dinner with excellent value and seasonal ingredients",
            course_count=3,
            menu_type='prix_fixe',
            base_price=Decimal('45.00'),
            price_per_person=Decimal('65.00'),
            min_party_size=2,
            max_party_size=10,
            advance_booking_days=1,
            vegetarian_available=True,
            vegan_available=False,
            gluten_free_available=True,
            wine_pairing_available=False,
            beverage_pairing_available=True,
            sommelier_required=False,
            is_seasonal=False,
            chef_table_exclusive=False,
            required_chef_level='line_cook',
            chef_notes="Classic French-inspired dishes with modern techniques",
            estimated_duration=90,
            pacing_interval=25,
            is_active=True,
        )
        
        # Create courses
        courses_data = [
            {
                'course_number': 1,
                'course_name': 'Seasonal Soup',
                'description': 'Creamy soup of the day with fresh herbs',
                'chef_notes': 'Use seasonal vegetables, adjust consistency',
                'prep_time': 15,
                'plating_time': 3,
                'presentation_time': 1,
                'main_ingredients': ['seasonal vegetables', 'cream', 'herbs'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['dairy'],
                'wine_pairing_notes': 'Light white wine',
                'beverage_pairing_notes': 'Sparkling water',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 1,
            },
            {
                'course_number': 2,
                'course_name': 'Main Course',
                'description': 'Grilled salmon with lemon butter sauce and roasted vegetables',
                'chef_notes': 'Cook to medium-rare, skin side down first',
                'prep_time': 20,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['salmon', 'lemon', 'butter', 'vegetables'],
                'complexity_level': 'medium',
                'wine_pairing_notes': 'Light-bodied white wine',
                'beverage_pairing_notes': 'Iced tea',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 2,
            },
            {
                'course_number': 3,
                'course_name': 'Dessert',
                'description': 'Chocolate mousse with fresh berries',
                'chef_notes': 'Chill for at least 2 hours before serving',
                'prep_time': 10,
                'plating_time': 3,
                'presentation_time': 1,
                'main_ingredients': ['chocolate', 'cream', 'berries'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['dairy'],
                'wine_pairing_notes': 'Sweet dessert wine',
                'beverage_pairing_notes': 'Coffee',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 3,
            },
        ]
        
        for course_data in courses_data:
            CourseDefinition.objects.create(template=template, **course_data)
        
        self.stdout.write(f'Created prix fixe template: {template.name}')

    def create_vegetarian_template(self):
        """Create a vegetarian tasting menu template"""
        template = CourseMenuTemplate.objects.create(
            name="Garden Tasting Journey",
            description="Plant-based tasting menu showcasing seasonal vegetables and creative techniques",
            course_count=5,
            menu_type='vegetarian',
            base_price=Decimal('80.00'),
            price_per_person=Decimal('120.00'),
            min_party_size=2,
            max_party_size=6,
            advance_booking_days=2,
            vegetarian_available=True,
            vegan_available=True,
            gluten_free_available=True,
            wine_pairing_available=True,
            beverage_pairing_available=True,
            sommelier_required=False,
            is_seasonal=False,
            chef_table_exclusive=False,
            required_chef_level='sous_chef',
            chef_notes="Focus on vegetable-forward dishes with creative techniques",
            estimated_duration=120,
            pacing_interval=20,
            is_active=True,
        )
        
        # Create courses
        courses_data = [
            {
                'course_number': 1,
                'course_name': 'Garden Welcome',
                'description': 'Vegetable crudités with herb dip',
                'chef_notes': 'Use colorful seasonal vegetables',
                'prep_time': 10,
                'plating_time': 5,
                'presentation_time': 1,
                'main_ingredients': ['vegetables', 'herbs', 'yogurt'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': True,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['dairy'],
                'wine_pairing_notes': 'Sauvignon Blanc',
                'beverage_pairing_notes': 'Herbal tea',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 1,
            },
            {
                'course_number': 2,
                'course_name': 'Earth & Sea',
                'description': 'Mushroom risotto with truffle oil',
                'chef_notes': 'Use arborio rice, stir constantly',
                'prep_time': 25,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['mushrooms', 'rice', 'truffle'],
                'complexity_level': 'medium',
                'is_vegetarian': True,
                'is_vegan': True,
                'is_gluten_free': False,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': ['gluten'],
                'wine_pairing_notes': 'Pinot Grigio',
                'beverage_pairing_notes': 'Sparkling water',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 2,
            },
            {
                'course_number': 3,
                'course_name': 'Harvest Bowl',
                'description': 'Roasted vegetable bowl with tahini dressing',
                'chef_notes': 'Roast vegetables separately for best texture',
                'prep_time': 20,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['vegetables', 'tahini', 'grains'],
                'complexity_level': 'medium',
                'is_vegetarian': True,
                'is_vegan': True,
                'is_gluten_free': True,
                'contains_nuts': True,
                'contains_dairy': False,
                'allergens': ['nuts', 'sesame'],
                'wine_pairing_notes': 'Light red wine',
                'beverage_pairing_notes': 'Kombucha',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 3,
            },
            {
                'course_number': 4,
                'course_name': 'Garden Pasta',
                'description': 'Fresh pasta with seasonal vegetables',
                'chef_notes': 'Cook pasta al dente',
                'prep_time': 20,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['pasta', 'vegetables', 'herbs'],
                'complexity_level': 'medium',
                'is_vegetarian': True,
                'is_vegan': True,
                'is_gluten_free': False,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': ['gluten'],
                'wine_pairing_notes': 'Chianti',
                'beverage_pairing_notes': 'Iced tea',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 4,
            },
            {
                'course_number': 5,
                'course_name': 'Sweet Garden',
                'description': 'Fruit sorbet with edible flowers',
                'chef_notes': 'Use seasonal fruits',
                'prep_time': 15,
                'plating_time': 3,
                'presentation_time': 1,
                'main_ingredients': ['fruits', 'flowers', 'herbs'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': True,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': [],
                'wine_pairing_notes': 'Moscato',
                'beverage_pairing_notes': 'Herbal tea',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 5,
            },
        ]
        
        for course_data in courses_data:
            CourseDefinition.objects.create(template=template, **course_data)
        
        self.stdout.write(f'Created vegetarian template: {template.name}')

    def create_seasonal_template(self):
        """Create a seasonal menu template"""
        template = CourseMenuTemplate.objects.create(
            name="Autumn Harvest Menu",
            description="Celebrate the flavors of autumn with seasonal ingredients",
            course_count=4,
            menu_type='seasonal',
            base_price=Decimal('75.00'),
            price_per_person=Decimal('95.00'),
            min_party_size=2,
            max_party_size=8,
            advance_booking_days=1,
            vegetarian_available=True,
            vegan_available=False,
            gluten_free_available=True,
            wine_pairing_available=True,
            beverage_pairing_available=True,
            sommelier_required=False,
            is_seasonal=True,
            season_months=[9, 10, 11],  # September, October, November
            holiday_specific=False,
            chef_table_exclusive=False,
            required_chef_level='sous_chef',
            chef_notes="Focus on autumn ingredients like squash, apples, and mushrooms",
            estimated_duration=100,
            pacing_interval=22,
            is_active=True,
        )
        
        # Create courses
        courses_data = [
            {
                'course_number': 1,
                'course_name': 'Autumn Soup',
                'description': 'Butternut squash soup with sage and pumpkin seeds',
                'chef_notes': 'Roast squash first for deeper flavor',
                'prep_time': 20,
                'plating_time': 5,
                'presentation_time': 1,
                'main_ingredients': ['butternut squash', 'sage', 'pumpkin seeds'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': True,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': ['nuts'],
                'wine_pairing_notes': 'Chardonnay',
                'beverage_pairing_notes': 'Apple cider',
                'pairing_intensity': 'light',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 1,
            },
            {
                'course_number': 2,
                'course_name': 'Forest Floor',
                'description': 'Wild mushroom salad with aged cheese',
                'chef_notes': 'Use variety of mushrooms for depth',
                'prep_time': 15,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['mushrooms', 'cheese', 'greens'],
                'complexity_level': 'medium',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['dairy'],
                'wine_pairing_notes': 'Pinot Noir',
                'beverage_pairing_notes': 'Mushroom tea',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 2,
            },
            {
                'course_number': 3,
                'course_name': 'Harvest Main',
                'description': 'Duck breast with apple compote and root vegetables',
                'chef_notes': 'Crispy skin, medium-rare meat',
                'prep_time': 25,
                'plating_time': 8,
                'presentation_time': 3,
                'main_ingredients': ['duck', 'apples', 'root vegetables'],
                'complexity_level': 'complex',
                'is_vegetarian': False,
                'is_vegan': False,
                'is_gluten_free': True,
                'contains_nuts': False,
                'contains_dairy': False,
                'allergens': [],
                'wine_pairing_notes': 'Cabernet Sauvignon',
                'beverage_pairing_notes': 'Apple juice',
                'pairing_intensity': 'bold',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 3,
            },
            {
                'course_number': 4,
                'course_name': 'Orchard Dessert',
                'description': 'Apple crumble with caramel sauce',
                'chef_notes': 'Use tart apples for balance',
                'prep_time': 15,
                'plating_time': 5,
                'presentation_time': 2,
                'main_ingredients': ['apples', 'caramel', 'oats'],
                'complexity_level': 'simple',
                'is_vegetarian': True,
                'is_vegan': False,
                'is_gluten_free': False,
                'contains_nuts': False,
                'contains_dairy': True,
                'allergens': ['gluten', 'dairy'],
                'wine_pairing_notes': 'Late harvest Riesling',
                'beverage_pairing_notes': 'Apple cider',
                'pairing_intensity': 'medium',
                'is_optional': False,
                'supplement_charge': Decimal('0.00'),
                'order': 4,
            },
        ]
        
        for course_data in courses_data:
            CourseDefinition.objects.create(template=template, **course_data)
        
        self.stdout.write(f'Created seasonal template: {template.name}')

    def create_sample_instances(self):
        """Create sample menu instances and pairings"""
        # Get templates
        tasting_template = CourseMenuTemplate.objects.get(name="Signature Tasting Experience")
        prix_fixe_template = CourseMenuTemplate.objects.get(name="Classic Prix Fixe Dinner")
        
        # Create sample instances
        tomorrow = date.today() + timedelta(days=1)
        
        # Tasting menu instance
        tasting_instance = CourseMenuInstance.objects.create(
            template=tasting_template,
            name="Anniversary Tasting - Johnson Family",
            table_number="Table 15",
            customer_count=4,
            final_price_per_person=Decimal('250.00'),
            total_price=Decimal('1000.00'),
            pricing_tier_applied='Premium',
            dietary_requirements=['gluten_free'],
            special_requests='Celebrating 25th anniversary, prefer quieter table',
            booking_date=tomorrow,
            booking_time=time(19, 30),
            status='confirmed',
        )
        
        # Prix fixe instance
        prix_fixe_instance = CourseMenuInstance.objects.create(
            template=prix_fixe_template,
            name="Business Dinner - Smith & Partners",
            table_number="Table 8",
            customer_count=3,
            final_price_per_person=Decimal('65.00'),
            total_price=Decimal('195.00'),
            pricing_tier_applied='Standard',
            dietary_requirements=[],
            special_requests='Business meeting, need efficient service',
            booking_date=tomorrow,
            booking_time=time(20, 0),
            status='confirmed',
        )
        
        # Create wine pairings for tasting menu
        tasting_courses = CourseDefinition.objects.filter(template=tasting_template)
        
        wine_pairings = [
            {
                'wine_name': 'Dom Pérignon',
                'wine_type': 'sparkling',
                'region': 'Champagne, France',
                'vintage': 2012,
                'pairing_notes': 'Perfect with oysters and celebration',
                'intensity_match': 'light',
                'price_per_glass': Decimal('25.00'),
                'price_per_bottle': Decimal('150.00'),
                'is_recommended': True,
            },
            {
                'wine_name': 'Chablis Grand Cru',
                'wine_type': 'white',
                'region': 'Burgundy, France',
                'vintage': 2020,
                'pairing_notes': 'Excellent with scallops and delicate dishes',
                'intensity_match': 'light',
                'price_per_glass': Decimal('18.00'),
                'price_per_bottle': Decimal('90.00'),
                'is_recommended': True,
            },
            {
                'wine_name': 'Domaine Drouhin Pinot Noir',
                'wine_type': 'red',
                'region': 'Oregon, USA',
                'vintage': 2019,
                'pairing_notes': 'Elegant with tomato salad and lamb',
                'intensity_match': 'medium',
                'price_per_glass': Decimal('22.00'),
                'price_per_bottle': Decimal('110.00'),
                'is_recommended': True,
            },
        ]
        
        for i, course in enumerate(tasting_courses[:3]):
            if i < len(wine_pairings):
                wine_data = wine_pairings[i]
                WinePairing.objects.create(
                    course_definition=course,
                    **wine_data
                )
        
        # Create beverage pairings
        beverage_pairings = [
            {
                'beverage_name': 'Herbal Infusion',
                'beverage_type': 'tea',
                'pairing_notes': 'Chamomile and lavender blend',
                'intensity_match': 'light',
                'price_per_serving': Decimal('8.00'),
                'is_recommended': True,
            },
            {
                'beverage_name': 'Craft Kombucha',
                'beverage_type': 'soda',
                'pairing_notes': 'Ginger and turmeric fermented tea',
                'intensity_match': 'medium',
                'price_per_serving': Decimal('6.00'),
                'is_recommended': False,
            },
            {
                'beverage_name': 'Cold Brew Coffee',
                'beverage_type': 'coffee',
                'pairing_notes': '24-hour steeped coffee concentrate',
                'intensity_match': 'bold',
                'price_per_serving': Decimal('5.00'),
                'is_recommended': True,
            },
        ]
        
        for i, course in enumerate(tasting_courses[:3]):
            if i < len(beverage_pairings):
                beverage_data = beverage_pairings[i]
                BeveragePairing.objects.create(
                    course_definition=course,
                    **beverage_data
                )
        
        self.stdout.write('Created sample instances and pairings')
