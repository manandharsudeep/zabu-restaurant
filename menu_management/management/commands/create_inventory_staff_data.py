from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from menu_management.inventory_models import *
from menu_management.staff_models import *
from decimal import Decimal
from datetime import date, timedelta, time
import random

class Command(BaseCommand):
    help = 'Create sample inventory and staff management data'

    def handle(self, *args, **options):
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found!'))
            return
        
        # Create storage locations
        locations_data = [
            ('Main Walk-in Cooler', 'walk_in_cooler', 'Primary refrigerated storage', 1000),
            ('Prep Station Cooler', 'reach_in_cooler', 'Preparation station refrigeration', 200),
            ('Main Freezer', 'freezer', 'Frozen goods storage', 800),
            ('Dry Storage A', 'dry_storage', 'Dry goods and pantry items', 1500),
            ('Bar Cooler', 'bar', 'Beverage and bar ingredients', 150),
            ('Display Case', 'display_case', 'Customer display items', 50),
        ]
        
        locations = []
        for name, loc_type, desc, capacity in locations_data:
            location, created = StorageLocation.objects.get_or_create(
                name=name,
                defaults={
                    'location_type': loc_type,
                    'description': desc,
                    'capacity': capacity,
                    'temperature_required': 4 if 'cooler' in name else -18 if 'freezer' in name else None,
                }
            )
            locations.append(location)
        
        # Create vendors
        vendors_data = [
            ('Fresh Produce Co', 'John Smith', 'john@freshproduce.com', '555-0101', '123 Farm Road, Agricultural City', 'FP001'),
            ('Meat Suppliers Inc', 'Sarah Johnson', 'sarah@meatsuppliers.com', '555-0102', '456 Butcher Street, Meatville', 'MS002'),
            ('Dairy Distributors', 'Mike Wilson', 'mike@dairydist.com', '555-0103', '789 Dairy Lane, Milk Town', 'DD003'),
            ('Beverage World', 'Lisa Brown', 'lisa@beverages.com', '555-0104', '321 Drink Avenue, Thirsty City', 'BW004'),
        ]
        
        vendors = []
        for name, contact, email, phone, address, code in vendors_data:
            vendor, created = Vendor.objects.get_or_create(
                vendor_code=code,
                defaults={
                    'name': name,
                    'contact_person': contact,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'is_preferred': random.choice([True, False]),
                    'lead_time_days': random.randint(1, 5),
                }
            )
            vendors.append(vendor)
        
        # Create inventory items
        items_data = [
            ('Ground Beef', 'Premium ground beef 80/20', 'MEAT001', None, 'kg', 'Meat', True, 7, 8.50, 9.20, 50, 25, 100),
            ('Chicken Breast', 'Boneless skinless chicken breast', 'MEAT002', None, 'kg', 'Meat', True, 5, 11.20, 12.50, 40, 20, 80),
            ('Lettuce', 'Fresh romaine lettuce', 'PROD001', None, 'kg', 'Produce', True, 3, 3.20, 3.80, 30, 15, 60),
            ('Tomatoes', 'Fresh vine tomatoes', 'PROD002', None, 'kg', 'Produce', True, 4, 4.10, 4.50, 25, 12, 50),
            ('Cheese', 'Mozzarella cheese shredded', 'DAIRY001', None, 'kg', 'Dairy', True, 14, 12.50, 13.80, 60, 30, 120),
            ('Pizza Dough', 'Fresh pizza dough balls', 'BAKE001', None, 'pcs', 'Bakery', True, 2, 2.30, 2.80, 100, 50, 200),
            ('Pasta', 'Dry spaghetti pasta', 'DRY001', None, 'kg', 'Dry Goods', False, 365, 3.80, 4.20, 80, 40, 160),
            ('Olive Oil', 'Extra virgin olive oil', 'DRY002', None, 'l', 'Dry Goods', False, 730, 15.60, 17.20, 20, 10, 40),
            ('Beer', 'Craft beer bottles', 'BEV001', None, 'bottle', 'Beverages', False, 180, 3.50, 4.20, 100, 40, 200),
            ('Wine', 'Red wine bottles', 'BEV002', None, 'bottle', 'Beverages', False, 365, 12.80, 15.60, 50, 20, 100),
        ]
        
        items = []
        for name, desc, sku, barcode, unit, category, perishable, shelf_life, std_cost, curr_cost, par, reorder, max_level in items_data:
            item, created = InventoryItem.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'description': desc,
                    'barcode': barcode,
                    'unit': unit,
                    'category': category,
                    'is_perishable': perishable,
                    'shelf_life_days': shelf_life,
                    'standard_cost': std_cost,
                    'current_cost': curr_cost,
                    'par_level': par,
                    'reorder_point': reorder,
                    'max_level': max_level,
                }
            )
            items.append(item)
        
        # Create inventory stock
        for item in items:
            for location in locations[:3]:  # Stock first 3 locations
                quantity = random.uniform(10, 100)
                InventoryStock.objects.get_or_create(
                    item=item,
                    location=location,
                    defaults={
                        'quantity': quantity,
                        'available_quantity': quantity * 0.9,  # 10% reserved
                    }
                )
        
        # Create inventory batches
        for item in items[:5]:  # Create batches for first 5 items
            for i in range(2):
                batch_num = f"B{item.sku}-{i+1:03d}"
                expiration_date = date.today() + timedelta(days=random.randint(5, 30))
                InventoryBatch.objects.get_or_create(
                    batch_number=batch_num,
                    defaults={
                        'item': item,
                        'vendor': random.choice(vendors),
                        'location': random.choice(locations[:2]),
                        'quantity': random.uniform(20, 100),
                        'unit_cost': item.current_cost,
                        'total_cost': float(item.current_cost) * random.uniform(20, 100),
                        'expiration_date': expiration_date,
                        'manufacture_date': expiration_date - timedelta(days=getattr(item, 'shelf_life', 30) or 30),
                    }
                )
        
        # Create staff profiles
        staff_data = [
            ('John Doe', 'EMP001', '555-1001', 'Jane Doe', '555-2001', date(2023, 1, 15), 'Head Chef', 'Kitchen', 22.50),
            ('Jane Smith', 'EMP002', '555-1002', 'Bob Smith', '555-2002', date(2023, 2, 20), 'Sous Chef', 'Kitchen', 18.75),
            ('Mike Johnson', 'EMP003', '555-1003', 'Mary Johnson', '555-2003', date(2023, 3, 10), 'Line Cook', 'Kitchen', 15.00),
            ('Sarah Williams', 'EMP004', '555-1004', 'Tom Williams', '555-2004', date(2023, 4, 5), 'Prep Cook', 'Kitchen', 14.00),
            ('David Brown', 'EMP005', '555-1005', 'Lisa Brown', '555-2005', date(2023, 5, 12), 'Server', 'Front of House', 12.50),
            ('Emily Davis', 'EMP006', '555-1006', 'Kevin Davis', '555-2006', date(2023, 6, 8), 'Bartender', 'Bar', 13.75),
            ('Chris Miller', 'EMP007', '555-1007', 'Amy Miller', '555-2007', date(2023, 7, 22), 'Host', 'Front of House', 11.50),
            ('Alex Wilson', 'EMP008', '555-1008', 'Sam Wilson', '555-2008', date(2023, 8, 14), 'Dishwasher', 'Kitchen', 11.00),
        ]
        
        staff_profiles = []
        for name, emp_id, phone, emergency, emergency_phone, hire_date, position, department, rate in staff_data:
            # Create user if doesn't exist
            username = name.lower().replace(' ', '.')
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'email': f'{username}@zaburestaurant.com',
                }
            )
            
            profile, created = StaffProfile.objects.get_or_create(
                employee_id=emp_id,
                defaults={
                    'user': user,
                    'phone': phone,
                    'emergency_contact': emergency,
                    'emergency_phone': emergency_phone,
                    'hire_date': hire_date,
                    'position': position,
                    'department': department,
                    'hourly_rate': rate,
                    'is_full_time': random.choice([True, False]),
                    'certifications': 'Food Handler Permit',
                    'skills': f'Experienced {position.lower()} with strong teamwork skills',
                }
            )
            staff_profiles.append(profile)
        
        # Create shift templates
        templates_data = [
            ('Morning Shift', time(7, 0), time(15, 0), 30, 'Early morning kitchen preparation'),
            ('Evening Shift', time(15, 0), time(23, 0), 30, 'Dinner service shift'),
            ('Closing Shift', time(22, 0), time(6, 0), 30, 'Overnight cleaning and prep'),
            ('Split Shift AM', time(10, 0), time(14, 0), 15, 'Morning service'),
            ('Split Shift PM', time(17, 0), time(21, 0), 15, 'Evening service'),
        ]
        
        templates = []
        for name, start, end, break_dur, desc in templates_data:
            template, created = ShiftTemplate.objects.get_or_create(
                name=name,
                defaults={
                    'start_time': start,
                    'end_time': end,
                    'break_duration': break_dur,
                    'description': desc,
                }
            )
            templates.append(template)
        
        # Create today's schedule
        today = date.today()
        for i, staff in enumerate(staff_profiles[:6]):  # Schedule first 6 staff
            template = templates[i % len(templates)]
            Schedule.objects.get_or_create(
                staff=staff,
                date=today,
                defaults={
                    'shift_template': template,
                    'start_time': template.start_time,
                    'end_time': template.end_time,
                    'break_duration': template.break_duration,
                    'role': staff.position,
                    'station': f'Station {i+1}',
                    'status': 'active',
                    'created_by': admin_user,
                }
            )
        
        # Create tasks
        tasks_data = [
            ('Daily Prep', 'Prepare vegetables and proteins for service', 'opening', 'high', 'Kitchen', 'Station 1', 120),
            ('Opening Checklist', 'Complete restaurant opening procedures', 'opening', 'high', 'All Areas', 'Front', 30),
            ('Inventory Count', 'Count key inventory items', 'mid_shift', 'medium', 'Kitchen', 'Storage', 45),
            ('Cleaning Duty', 'Clean and sanitize workstations', 'closing', 'medium', 'Kitchen', 'All Stations', 60),
            ('Order Supplies', 'Place orders for low stock items', 'mid_shift', 'medium', 'Office', 'Manager Office', 30),
            ('Staff Meeting', 'Weekly team meeting', 'other', 'low', 'Meeting Room', 'Conference', 60),
        ]
        
        for i, (title, desc, task_type, priority, location, station, duration) in enumerate(tasks_data):
            assigned_to = staff_profiles[i % len(staff_profiles)]
            due_date = timezone.now() + timedelta(hours=random.randint(1, 8))
            
            Task.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'task_type': task_type,
                    'priority': priority,
                    'assigned_to': assigned_to,
                    'assigned_by': admin_user,
                    'location': location,
                    'station': station,
                    'due_date': due_date,
                    'estimated_duration': duration,
                    'status': random.choice(['pending', 'in_progress', 'completed']),
                }
            )
        
        # Create sample transactions
        transaction_types = ['receive', 'issue', 'waste', 'adjustment']
        for i in range(10):
            item = random.choice(items)
            location = random.choice(locations)
            trans_type = random.choice(transaction_types)
            
            InventoryTransaction.objects.create(
                item=item,
                batch=random.choice(item.batches.all()) if item.batches.exists() else None,
                location=location,
                transaction_type=trans_type,
                quantity=random.uniform(1, 50),
                unit_cost=item.current_cost,
                total_cost=float(item.current_cost) * random.uniform(1, 50),
                reason_code=random.choice(['normal_usage', 'spoilage', 'damage', 'physical_variance']),
                notes=f'Sample {trans_type} transaction',
                created_by=admin_user,
            )
        
        # Create waste records
        waste_types = ['spoilage', 'prep_waste', 'over_production', 'customer_return']
        for i in range(5):
            item = random.choice(items)
            
            WasteRecord.objects.create(
                item=item,
                location=random.choice(locations),
                batch=random.choice(item.batches.all()) if item.batches.exists() else None,
                waste_type=random.choice(waste_types),
                quantity=random.uniform(0.5, 5),
                estimated_cost=float(item.current_cost) * random.uniform(0.5, 5),
                reason=f'Sample waste record for {item.name}',
                reported_by=admin_user,
                is_approved=random.choice([True, False]),
            )
        
        self.stdout.write(self.style.SUCCESS('Sample inventory and staff data created successfully!'))
        self.stdout.write(f'Created {len(locations)} storage locations')
        self.stdout.write(f'Created {len(vendors)} vendors')
        self.stdout.write(f'Created {len(items)} inventory items')
        self.stdout.write(f'Created {len(staff_profiles)} staff profiles')
        self.stdout.write(f'Created {len(templates)} shift templates')
        self.stdout.write(f'Created sample schedules, tasks, transactions, and waste records')
