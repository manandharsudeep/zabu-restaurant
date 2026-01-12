# Generated migration for comprehensive implementation models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('menu_management', '0013_recipemenuitemlink'),
    ]

    operations = [
        # POS Integration Models
        migrations.CreateModel(
            name='POSIntegration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('integration_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('pos_system', models.CharField(choices=[('square', 'Square'), ('toast', 'Toast'), ('clover', 'Clover'), ('lightspeed', 'Lightspeed'), ('shopify', 'Shopify POS')], max_length=20)),
                ('location_name', models.CharField(max_length=100)),
                ('api_key', models.CharField(max_length=255)),
                ('api_secret', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('sync_status', models.CharField(choices=[('pending', 'Pending'), ('syncing', 'Syncing'), ('success', 'Success'), ('error', 'Error')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='POSOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pos_order_id', models.CharField(max_length=100)),
                ('order_data', models.JSONField(default=dict)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('preparing', 'Preparing'), ('ready', 'Ready'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('order_time', models.DateTimeField(auto_now_add=True)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.posintegration')),
            ],
        ),
        migrations.CreateModel(
            name='POSMenuSync',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('menu_data', models.JSONField(default=dict)),
                ('sync_status', models.CharField(choices=[('pending', 'Pending'), ('syncing', 'Syncing'), ('success', 'Success'), ('error', 'Error')], default='pending', max_length=20)),
                ('items_synced', models.IntegerField(default=0)),
                ('sync_time', models.DateTimeField(auto_now_add=True)),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.posintegration')),
            ],
        ),

        # Delivery Platform Models
        migrations.CreateModel(
            name='DeliveryPlatform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('platform_name', models.CharField(choices=[('uber_eats', 'Uber Eats'), ('doordash', 'DoorDash'), ('grubhub', 'Grubhub'), ('foodpanda', 'Foodpanda'), ('zomato', 'Zomato')], max_length=20)),
                ('api_key', models.CharField(max_length=255)),
                ('webhook_url', models.URLField(blank=True, null=True)),
                ('commission_rate', models.DecimalField(decimal_places=2, default=0.15, max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform_order_id', models.CharField(max_length=100)),
                ('customer_name', models.CharField(max_length=100)),
                ('customer_phone', models.CharField(max_length=20)),
                ('delivery_address', models.TextField()),
                ('order_items', models.JSONField(default=list)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('delivery_fee', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('received', 'Received'), ('confirmed', 'Confirmed'), ('preparing', 'Preparing'), ('ready_for_pickup', 'Ready for Pickup'), ('out_for_delivery', 'Out for Delivery'), ('delivered', 'Delivered')], default='received', max_length=25)),
                ('estimated_delivery_time', models.DateTimeField(blank=True, null=True)),
                ('order_time', models.DateTimeField(auto_now_add=True)),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.deliveryplatform')),
            ],
        ),

        # Order Orchestration Models
        migrations.CreateModel(
            name='UnifiedOrderQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('order_type', models.CharField(choices=[('pos', 'POS'), ('delivery', 'Delivery'), ('online', 'Online'), ('phone', 'Phone')], max_length=20)),
                ('priority', models.IntegerField(choices=[(1, 'Low'), (2, 'Normal'), (3, 'High'), (4, 'Urgent')], default=2)),
                ('status', models.CharField(choices=[('received', 'Received'), ('confirmed', 'Confirmed'), ('preparing', 'Preparing'), ('ready', 'Ready'), ('completed', 'Completed')], default='received', max_length=20)),
                ('order_data', models.JSONField(default=dict)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order_time', models.DateTimeField(auto_now_add=True)),
                ('estimated_completion', models.DateTimeField(blank=True, null=True)),
                ('completed_time', models.DateTimeField(blank=True, null=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='OrderPrioritization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('rule_type', models.CharField(choices=[('vip_customer', 'VIP Customer'), ('large_order', 'Large Order'), ('repeat_customer', 'Repeat Customer'), ('time_sensitive', 'Time Sensitive')], max_length=20)),
                ('weight', models.DecimalField(decimal_places=2, default=1.0, max_digits=3)),
                ('conditions', models.JSONField(default=dict)),
                ('priority', models.IntegerField(choices=[(1, 'Low'), (2, 'Normal'), (3, 'High'), (4, 'Urgent')], default=2)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='UnifiedOrderBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('batch_name', models.CharField(max_length=100)),
                ('orders', models.ManyToManyField(related_name='batches', to='menu_management.unifiedorderqueue')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),

        # Real-time Order Models
        migrations.CreateModel(
            name='RealTimeOrderTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracking_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('current_step', models.CharField(choices=[('order_received', 'Order Received'), ('preparation_started', 'Preparation Started'), ('cooking', 'Cooking'), ('plating', 'Plating'), ('quality_check', 'Quality Check'), ('ready_for_pickup', 'Ready for Pickup'), ('delivered', 'Delivered')], default='order_received', max_length=30)),
                ('progress_percentage', models.IntegerField(default=0)),
                ('estimated_completion', models.DateTimeField(blank=True, null=True)),
                ('actual_completion', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='real_time_tracking', to='menu_management.unifiedorderqueue')),
            ],
        ),
        migrations.CreateModel(
            name='SpecialRequestManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('request_type', models.CharField(choices=[('allergy', 'Allergy'), ('dietary', 'Dietary'), ('preference', 'Preference'), ('customization', 'Customization')], max_length=20)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('acknowledged', 'Acknowledged'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('urgent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.unifiedorderqueue')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
        ),

        # Customer Service Models
        migrations.CreateModel(
            name='VIPCustomerManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vip_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
                ('vip_level', models.CharField(choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold'), ('platinum', 'Platinum')], default='bronze', max_length=20)),
                ('total_orders', models.IntegerField(default=0)),
                ('total_spent', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('preferences', models.JSONField(default=dict)),
                ('notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='CustomerFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('rating', models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])),
                ('comment', models.TextField(blank=True)),
                ('feedback_type', models.CharField(choices=[('food_quality', 'Food Quality'), ('service', 'Service'), ('delivery', 'Delivery'), ('ambiance', 'Ambiance'), ('overall', 'Overall')], max_length=20)),
                ('sentiment', models.CharField(choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')], max_length=10)),
                ('is_resolved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='menu_management.unifiedorderqueue')),
            ],
        ),

        # Kitchen Optimization Models
        migrations.CreateModel(
            name='AdvancedScheduling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schedule_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('shift_date', models.DateField()),
                ('shift_type', models.CharField(choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('evening', 'Evening'), ('night', 'Night')], max_length=20)),
                ('predicted_orders', models.IntegerField(default=0)),
                ('required_staff', models.IntegerField(default=1)),
                ('optimal_start_time', models.TimeField(blank=True, null=True)),
                ('optimal_end_time', models.TimeField(blank=True, null=True)),
                ('efficiency_score', models.DecimalField(decimal_places=2, default=0.8, max_digits=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='KitchenStationAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assignment_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('station_name', models.CharField(max_length=50)),
                ('capacity', models.IntegerField(default=1)),
                ('current_load', models.IntegerField(default=0)),
                ('efficiency_rating', models.DecimalField(decimal_places=2, default=0.8, max_digits=3)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='PackagingManagement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('packaging_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('packaging_type', models.CharField(choices=[('standard', 'Standard'), ('premium', 'Premium'), ('eco_friendly', 'Eco-Friendly'), ('custom', 'Custom')], max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=6)),
                ('inventory_quantity', models.IntegerField(default=0)),
                ('reorder_level', models.IntegerField(default=10)),
                ('supplier', models.CharField(max_length=100, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),

        # Multi-location Models
        migrations.CreateModel(
            name='CloudKitchenLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=50)),
                ('state', models.CharField(max_length=50)),
                ('country', models.CharField(max_length=50)),
                ('postal_code', models.CharField(max_length=20)),
                ('phone', models.CharField(max_length=20, blank=True)),
                ('email', models.EmailField(blank=True)),
                ('capacity', models.IntegerField(default=50)),
                ('operating_hours', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu_management.virtualbrand')),
            ],
        ),
        migrations.CreateModel(
            name='HubAndSpokeOperations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('hub_location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hub_operations', to='menu_management.cloudkitchenlocation')),
                ('spoke_locations', models.ManyToManyField(related_name='spoke_operations', to='menu_management.cloudkitchenlocation')),
                ('operation_type', models.CharField(choices=[('preparation', 'Preparation'), ('packaging', 'Packaging'), ('distribution', 'Distribution'), ('quality_control', 'Quality Control')], max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('maintenance', 'Maintenance')], default='active', max_length=20)),
                ('efficiency_metrics', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
