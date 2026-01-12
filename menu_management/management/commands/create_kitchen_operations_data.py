from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from menu_management.kitchen_operations_models import *
from menu_management.routing_models import KitchenStation
from decimal import Decimal
from datetime import date, time, datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create sample kitchen operations data'

    def handle(self, *args, **options):
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found!'))
            return
        
        # Create order sources
        sources_data = [
            ('POS System', 'pos', 'http://localhost:8080/api', 'pos123', True),
            ('Online Ordering', 'online', 'http://localhost:8081/api', 'web123', True),
            ('Uber Eats', 'delivery', 'https://api.uber.com', 'uber123', True),
            ('DoorDash', 'delivery', 'https://api.doordash.com', 'dd123', True),
            ('Phone Orders', 'phone', '', '', True),
        ]
        
        sources = []
        for name, source_type, endpoint, key, active in sources_data:
            source, created = OrderSource.objects.get_or_create(
                name=name,
                defaults={
                    'source_type': source_type,
                    'api_endpoint': endpoint,
                    'api_key': key,
                    'is_active': active,
                }
            )
            sources.append(source)
        
        # Create kitchen orders
        orders_data = [
            # Regular dine-in orders
            {
                'order_type': 'dine_in',
                'table_number': '12',
                'customer_name': 'John Smith',
                'priority': 'normal',
                'special_instructions': 'Extra napkins please',
                'is_rush_order': False,
                'is_vip_order': False,
                'estimated_prep_time': 25,
                'items': [
                    {'name': 'Classic Burger', 'quantity': 2, 'modifications': ['No onions', 'Extra cheese']},
                    {'name': 'Caesar Salad', 'quantity': 1, 'modifications': []},
                ]
            },
            {
                'order_type': 'dine_in',
                'table_number': '8',
                'customer_name': 'Mary Johnson',
                'priority': 'normal',
                'special_instructions': 'Allergic to nuts',
                'is_rush_order': False,
                'is_vip_order': False,
                'estimated_prep_time': 30,
                'items': [
                    {'name': 'Margherita Pizza', 'quantity': 1, 'modifications': ['Extra basil']},
                    {'name': 'Spaghetti Carbonara', 'quantity': 1, 'modifications': []},
                ]
            },
            # Takeout orders
            {
                'order_type': 'takeout',
                'customer_name': 'Bob Wilson',
                'priority': 'normal',
                'special_instructions': 'No ice in drinks',
                'is_rush_order': False,
                'is_vip_order': False,
                'estimated_prep_time': 20,
                'items': [
                    {'name': 'Grilled Chicken', 'quantity': 1, 'modifications': ['Well done']},
                    {'name': 'Classic Burger', 'quantity': 1, 'modifications': []},
                ]
            },
            # Delivery orders
            {
                'order_type': 'delivery',
                'customer_name': 'Alice Brown',
                'priority': 'normal',
                'special_instructions': 'Leave at door',
                'is_rush_order': False,
                'is_vip_order': False,
                'estimated_prep_time': 35,
                'items': [
                    {'name': 'Margherita Pizza', 'quantity': 2, 'modifications': ['Half pepperoni']},
                    {'name': 'Caesar Salad', 'quantity': 1, 'modifications': ['No croutons']},
                ]
            },
            # Rush order
            {
                'order_type': 'dine_in',
                'table_number': 'VIP-1',
                'customer_name': 'VIP Customer',
                'priority': 'urgent',
                'special_instructions': 'VIP guest - prioritize',
                'is_rush_order': True,
                'is_vip_order': True,
                'estimated_prep_time': 15,
                'items': [
                    {'name': 'Grilled Chicken', 'quantity': 1, 'modifications': ['Medium rare']},
                    {'name': 'Margherita Pizza', 'quantity': 1, 'modifications': ['Extra cheese']},
                ]
            },
        ]
        
        orders = []
        for order_data in orders_data:
            order = KitchenOrder.objects.create(
                source=random.choice(sources),
                order_type=order_data['order_type'],
                table_number=order_data.get('table_number', ''),
                customer_name=order_data['customer_name'],
                priority=order_data['priority'],
                special_instructions=order_data['special_instructions'],
                is_rush_order=order_data['is_rush_order'],
                is_vip_order=order_data['is_vip_order'],
                estimated_prep_time=order_data['estimated_prep_time'],
                confirmed_by=admin_user,
                confirmed_at=timezone.now(),
            )
            
            # Create order items
            for item_data in order_data['items']:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item_data['name'],
                    quantity=item_data['quantity'],
                    modifications=item_data['modifications'],
                    preparation_time=random.randint(10, 25),
                )
            
            orders.append(order)
        
        # Create prep items
        prep_items_data = [
            ('Burger Patties', 'Ground beef patties for burgers', 'Meat', 'Grill and shape', 15, Decimal('2.5'), 'kg', 5.0, 2.0),
            ('Pizza Dough', 'Fresh pizza dough balls', 'Bakery', 'Mix and proof', 30, Decimal('1.2'), 'kg', 8.0, 3.0),
            ('Caesar Dressing', 'Homemade Caesar dressing', 'Prep', 'Emulsify and season', 20, Decimal('0.5'), 'l', 3.0, 1.0),
            ('Chicken Marinade', 'Marinade for grilled chicken', 'Prep', 'Mix ingredients', 10, Decimal('0.3'), 'l', 4.0, 2.0),
            ('Vegetable Mix', 'Cut vegetables for salads', 'Prep', 'Wash and chop', 25, Decimal('1.0'), 'kg', 6.0, 2.5),
            ('Soup Base', 'Homemade soup stock base', 'Prep', 'Simmer and strain', 120, Decimal('5.0'), 'l', 10.0, 4.0),
            ('Bread Croutons', 'Croutons for Caesar salad', 'Prep', 'Cut and toast', 15, Decimal('0.8'), 'kg', 2.0, 1.0),
            ('Pasta Sauce', 'Fresh marinara sauce', 'Prep', 'Cook and season', 45, Decimal('2.0'), 'l', 5.0, 2.5),
        ]
        
        prep_items = []
        for name, desc, category, method, prep_time, cost, unit, par, shelf_life in prep_items_data:
            item = PrepItem.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'category': category,
                    'prep_method': method,
                    'prep_time': prep_time,
                    'batch_size': random.randint(5, 20),
                    'yield_quantity': par * 1.2,
                    'yield_unit': unit,
                    'shelf_life_hours': shelf_life * 24,
                    'par_level': par,
                    'ingredient_cost': cost,
                    'labor_cost': float(cost) * 0.3,
                    'total_cost': float(cost) * 1.3,
                }
            )[0]
            prep_items.append(item)
        
        # Create prep tasks for today
        today = date.today()
        prep_tasks = []
        for i, prep_item in enumerate(prep_items[:5]):  # Create tasks for first 5 items
            task = PrepTask.objects.create(
                prep_item=prep_item,
                scheduled_date=today,
                scheduled_time=time(8 + i, 0),  # Stagger start times
                priority=random.choice(['low', 'medium', 'high']),
                target_quantity=prep_item.par_level,
                assigned_to=admin_user,
                created_by=admin_user,
            )
            prep_tasks.append(task)
        
        # Create prep checklists
        stations = KitchenStation.objects.filter(is_active=True)[:3]
        checklists_data = [
            ('Opening Checklist', 'opening', time(7, 0), time(8, 0)),
            ('Mid-shift Prep', 'mid_shift', time(14, 0), time(14, 30)),
            ('Closing Checklist', 'closing', time(22, 0), time(23, 0)),
        ]
        
        checklists = []
        for station in stations:
            for name, checklist_type, start_time, end_time in checklists_data:
                checklist = PrepChecklist.objects.create(
                    station=station,
                    name=f"{name} - {station.name}",
                    checklist_date=today,
                    checklist_type=checklist_type,
                    start_time=start_time,
                    end_time=end_time,
                    assigned_to=admin_user,
                    items=[
                        {'text': 'Clean and sanitize station', 'completed': False},
                        {'text': 'Check equipment functionality', 'completed': False},
                        {'text': 'Restock supplies', 'completed': False},
                        {'text': 'Review prep list', 'completed': False},
                    ]
                )
                checklists.append(checklist)
        
        # Create digital thermometers
        thermometers_data = [
            ('Main Cooler Probe', 'Main Walk-in Cooler', 'probe', '2024-01-01', '2024-04-01'),
            ('Grill Surface IR', 'Grill Station', 'infrared', '2024-01-01', '2024-04-01'),
            ('Freezer Probe', 'Main Freezer', 'probe', '2024-01-01', '2024-04-01'),
            ('Holding Unit', 'Hot Holding Unit', 'ambient', '2024-01-01', '2024-04-01'),
        ]
        
        thermometers = []
        for name, location, thermo_type, last_cal, next_cal in thermometers_data:
            thermometer, created = DigitalThermometer.objects.get_or_create(
                device_id=f"TEMP_{name.upper().replace(' ', '_')}",
                defaults={
                    'name': name,
                    'location': location,
                    'thermometer_type': thermo_type,
                    'last_calibration': datetime.strptime(last_cal, '%Y-%m-%d').date(),
                    'next_calibration': datetime.strptime(next_cal, '%Y-%m-%d').date(),
                    'is_connected': random.choice([True, False]),
                    'is_active': True,
                }
            )
            thermometers.append(thermometer)
        
        # Create sample temperature logs (commented out for now due to constraint issues)
        # temp_logs = []
        # for thermometer in thermometers:
        #     for i in range(3):  # Create 3 logs per thermometer
        #         temp_log = KitchenTemperatureLog.objects.create(
        #             thermometer=thermometer,
        #             log_type=random.choice(['cooking', 'cooling', 'holding', 'storage']),
        #             location=thermometer.location,
        #             food_item=f"Sample Item {i+1}",
        #             current_temp=Decimal(str(random.uniform(2, 8))),
        #             target_temp=Decimal('4.0'),
        #             min_safe_temp=Decimal('1.0'),
        #             max_safe_temp=Decimal('7.0'),
        #             logged_by=admin_user,
        #         )
        #         
        #         # Check if within range and set the field
        #         temp_log.is_within_range = temp_log.min_safe_temp <= temp_log.current_temp <= temp_log.max_safe_temp
        #         if not temp_log.is_within_range:
        #             temp_log.alert_triggered = True
        #             temp_log.alert_level = 'high'
        #         
        #         temp_logs.append(temp_log)
        
        # Create sanitation checklists
        sanitation_checklists = []
        areas = ['Main Kitchen', 'Prep Area', 'Dishwashing Station', 'Storage Areas']
        
        for area in areas:
            checklist = SanitationChecklist.objects.create(
                area=area,
                equipment=f"{area} Equipment",
                checklist_date=today,
                checklist_type='opening',
                assigned_to=admin_user,
                items=[
                    {'text': 'Clean all surfaces', 'completed': random.choice([True, False])},
                    {'text': 'Sanitize equipment', 'completed': random.choice([True, False])},
                    {'text': 'Check temperature logs', 'completed': random.choice([True, False])},
                    {'text': 'Restock cleaning supplies', 'completed': random.choice([True, False])},
                ],
                is_completed=random.choice([True, False]),
                completed_at=timezone.now() if random.choice([True, False]) else None,
            )
            sanitation_checklists.append(checklist)
        
        # Create course menus
        course_menus = []
        for i in range(2):  # Create 2 course menus
            menu = CourseMenu.objects.create(
                name=f"Tasting Menu {i+1}",
                table_number=f"{i+5}",
                customer_count=random.randint(2, 4),
                courses=[
                    {'name': 'Appetizer', 'prep_time': 15},
                    {'name': 'Main Course', 'prep_time': 25},
                    {'name': 'Dessert', 'prep_time': 10},
                ],
                current_course=0,
                pacing_interval=15,
                server=admin_user,
                start_time=timezone.now(),
            )
            
            # Create course timings
            for j, course in enumerate(menu.courses):
                start_time = menu.start_time + timedelta(minutes=j * menu.pacing_interval)
                CourseTiming.objects.create(
                    course_menu=menu,
                    course_number=j + 1,
                    course_name=course['name'],
                    scheduled_start=start_time,
                    scheduled_completion=start_time + timedelta(minutes=course['prep_time']),
                    status='pending',
                )
            
            course_menus.append(menu)
        
        self.stdout.write(self.style.SUCCESS('Sample kitchen operations data created successfully!'))
        self.stdout.write(f'Created {len(sources)} order sources')
        self.stdout.write(f'Created {len(orders)} kitchen orders')
        self.stdout.write(f'Created {len(prep_items)} prep items')
        self.stdout.write(f'Created {len(prep_tasks)} prep tasks')
        self.stdout.write(f'Created {len(checklists)} prep checklists')
        self.stdout.write(f'Created {len(thermometers)} digital thermometers')
        self.stdout.write(f'Created {len(sanitation_checklists)} sanitation checklists')
        self.stdout.write(f'Created {len(course_menus)} course menus')
