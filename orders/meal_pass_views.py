from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from decimal import Decimal
import json
import random

from .models import MealPass, MealPassSubscription, MealPassUsage, MealPassBenefit, DailyMealOption, MealPassSelection
from orders.models import Order, OrderItem, MenuItem

def meal_pass_options(request):
    """Display meal pass options for customers"""
    # Get all active meal passes
    weekly_passes = MealPass.objects.filter(tier='weekly', is_active=True).order_by('price')
    monthly_passes = MealPass.objects.filter(tier='monthly', is_active=True).order_by('price')
    super_special_passes = MealPass.objects.filter(tier='super_special', is_active=True).order_by('price')
    
    # Add pre-order information to meal passes
    for meal_pass in weekly_passes:
        if 'Premium' in meal_pass.name:
            meal_pass.preorder_days = 3
            meal_pass.preorder_description = "Pre-order meals 3 days in advance"
        else:
            meal_pass.preorder_days = 7
            meal_pass.preorder_description = "Pre-order meals 7 days in advance"
    
    for meal_pass in monthly_passes:
        meal_pass.preorder_days = 7
        meal_pass.preorder_description = "Pre-order meals 7 days in advance"
    
    for meal_pass in super_special_passes:
        meal_pass.preorder_days = 7
        meal_pass.preorder_description = "Pre-order meals 7 days in advance"
    
    # Get user's current subscriptions if authenticated
    user_subscriptions = []
    if request.user.is_authenticated:
        user_subscriptions = MealPassSubscription.objects.filter(
            user=request.user,
            status='active',
            end_date__gt=timezone.now()
        ).select_related('meal_pass')
    
    context = {
        'weekly_passes': weekly_passes,
        'monthly_passes': monthly_passes,
        'super_special_passes': super_special_passes,
        'user_subscriptions': user_subscriptions,
    }
    
    return render(request, 'meal_pass/meal_pass_options.html', context)

def meal_pass_billing(request, pass_id):
    """Display billing page for meal pass purchase"""
    meal_pass = get_object_or_404(MealPass, id=pass_id, is_active=True)
    
    context = {
        'meal_pass': meal_pass,
    }
    
    return render(request, 'meal_pass/meal_pass_billing.html', context)

@login_required
def purchase_meal_pass(request, pass_id):
    """Handle meal pass purchase with payment processing"""
    meal_pass = get_object_or_404(MealPass, id=pass_id, is_active=True)
    
    # Check for ANY existing active subscription (not just the same meal pass)
    existing_subscription = MealPassSubscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gt=timezone.now()
    ).first()
    
    if existing_subscription:
        messages.warning(request, f'You already have an active {existing_subscription.meal_pass.name} subscription. You cannot purchase multiple meal passes simultaneously.')
        return redirect('meal_pass_options')
    
    # PAYMENT PROCESSING - ALLOW CASH ONLY
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        
        # Allow cash purchases, block other payment methods
        if payment_method != 'cash':
            messages.error(request, ' Payment processing is currently not implemented for this payment method. Please choose "Cash on Delivery" and try again.')
            return redirect('purchase_meal_pass', pass_id)
        
        try:
            # Create new subscription for cash payment
            start_date = timezone.now()
            end_date = start_date + timedelta(days=meal_pass.duration_days)
            
            subscription = MealPassSubscription.objects.create(
                user=request.user,
                meal_pass=meal_pass,
                start_date=start_date,
                end_date=end_date,
                meals_remaining=meal_pass.meals_per_period,
                total_meals=meal_pass.meals_per_period,
                payment_method='cash',
                payment_id=f"MP_{timezone.now().strftime('%Y%m%d%H%M%S')}_{request.user.id}"
            )
            
            messages.success(request, f'Successfully purchased {meal_pass.name}! You have {meal_pass.meals_per_period} meals available. Please pay cash on delivery.')
            return redirect('meal_pass_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error purchasing meal pass: {str(e)}')
            return redirect('meal_pass_options')
    
    # Calculate price per day
    price_per_day = meal_pass.price / meal_pass.duration_days
    
    context = {
        'meal_pass': meal_pass,
        'price_per_day': price_per_day,
    }
    
    return render(request, 'meal_pass/purchase_meal_pass.html', context)

@login_required
def meal_pass_dashboard(request):
    """User's meal pass dashboard"""
    # Get user's active subscriptions
    active_subscriptions = MealPassSubscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gt=timezone.now()
    ).select_related('meal_pass').order_by('-end_date')
    
    # Calculate meals used for each subscription
    for subscription in active_subscriptions:
        subscription.meals_used = subscription.total_meals - subscription.meals_remaining
    
    # Get meal pass usage history
    usage_history = MealPassUsage.objects.filter(
        user=request.user
    ).select_related('subscription__meal_pass', 'order').order_by('-used_at')[:10]
    
    # Calculate savings
    total_savings = MealPassUsage.objects.filter(user=request.user).aggregate(
        total=Sum('amount_saved')
    )['total'] or 0
    
    context = {
        'active_subscriptions': active_subscriptions,
        'usage_history': usage_history,
        'total_savings': total_savings,
        'last_updated': timezone.now().isoformat(),  # Add timestamp for cache busting
    }
    
    response = render(request, 'meal_pass/meal_pass_dashboard.html', context)
    # Add cache control headers to prevent browser caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def use_meal_pass(request):
    """Use meal pass for an order"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            
            # Get the order
            order = get_object_or_404(Order, id=order_id, customer=request.user)
            
            # Get user's active subscriptions
            active_subscription = MealPassSubscription.objects.filter(
                user=request.user,
                status='active',
                end_date__gt=timezone.now(),
                meals_remaining__gt=0
            ).first()
            
            if not active_subscription:
                return JsonResponse({'success': False, 'message': 'No active meal pass available'})
            
            # Calculate discount
            original_total = order.total_price
            discount_amount = original_total * (active_subscription.meal_pass.discount_percentage / 100)
            new_total = original_total - discount_amount
            
            # Update order total
            order.total_price = new_total
            order.save()
            
            # Use meal
            if active_subscription.use_meal():
                # Record usage
                MealPassUsage.objects.create(
                    subscription=active_subscription,
                    user=request.user,
                    order=order,
                    amount_saved=discount_amount
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Meal pass used! Saved ${discount_amount:.2f}',
                    'new_total': float(new_total),
                    'meals_remaining': active_subscription.meals_remaining
                })
            else:
                return JsonResponse({'success': False, 'message': 'No meals remaining in your pass'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def meal_pass_benefits(request):
    """Display meal pass benefits"""
    if not request.user.is_authenticated:
        return redirect('customer_login')
    
    # Get user's active subscriptions
    active_subscriptions = MealPassSubscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gt=timezone.now()
    ).select_related('meal_pass')
    
    # Get benefits for user's meal passes
    benefits = []
    for subscription in active_subscriptions:
        pass_benefits = MealPassBenefit.objects.filter(
            meal_pass=subscription.meal_pass,
            is_active=True
        )
        benefits.extend(pass_benefits)
    
    context = {
        'active_subscriptions': active_subscriptions,
        'benefits': benefits,
    }
    
    return render(request, 'meal_pass/meal_pass_benefits.html', context)

@csrf_exempt
def check_meal_pass_availability(request):
    """Check if user has available meal passes"""
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            active_subscription = MealPassSubscription.objects.filter(
                user=request.user,
                status='active',
                end_date__gt=timezone.now(),
                meals_remaining__gt=0
            ).first()
            
            if active_subscription:
                return JsonResponse({
                    'available': True,
                    'pass_name': active_subscription.meal_pass.name,
                    'meals_remaining': active_subscription.meals_remaining,
                    'discount_percentage': active_subscription.meal_pass.discount_percentage
                })
            else:
                return JsonResponse({'available': False})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'available': False})

@login_required
def daily_meal_selection(request, date_str=None):
    """Display daily meal selection for meal pass holders"""
    # Get subscription_id from request parameters
    subscription_id = request.GET.get('subscription_id')
    
    # Get user's active subscriptions
    active_subscriptions = MealPassSubscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gt=timezone.now()
    ).select_related('meal_pass')
    
    if not active_subscriptions:
        messages.warning(request, 'You need an active meal pass to select daily meals.')
        return redirect('meal_pass_options')
    
    # If subscription_id is provided, use that specific subscription
    if subscription_id:
        try:
            selected_subscription = active_subscriptions.get(id=subscription_id)
            print(f"DEBUG: Using specific subscription: {selected_subscription.meal_pass.name}")
        except MealPassSubscription.DoesNotExist:
            messages.error(request, 'Invalid subscription selected.')
            return redirect('meal_pass_dashboard')
    else:
        # Fall back to first subscription if no specific one requested
        selected_subscription = active_subscriptions.first()
        print(f"DEBUG: Using first subscription: {selected_subscription.meal_pass.name}")
    
    # Store the selected subscription in session for use in meal selection
    request.session['selected_subscription_id'] = str(selected_subscription.id)
    request.session.modified = True
    
    # Get target date (today or specified date)
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()
    
    # Calculate previous and next dates for navigation
    from datetime import timedelta
    previous_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)
    
    # Check if user already selected a meal for this date
    existing_selection = MealPassSelection.objects.filter(
        user=request.user,
        selection_date=target_date
    ).first()
    
    # Get daily meal options for target date
    try:
        daily_options = DailyMealOption.objects.get(date=target_date, is_active=True)
    except DailyMealOption.DoesNotExist:
        # Create meal options on-demand if they don't exist
        from orders.models import MenuItem
        import random
        
        available_items = list(MenuItem.objects.filter(available=True))
        if len(available_items) >= 5:
            selected_items = random.sample(available_items, 5)
            daily_options = DailyMealOption.objects.create(
                date=target_date,
                meal_option_1=selected_items[0],
                meal_option_2=selected_items[1],
                meal_option_3=selected_items[2],
                meal_option_4=selected_items[3],
                meal_option_5=selected_items[4],
            )
            messages.info(request, f'Created meal options for {target_date}')
        else:
            messages.error(request, f'Not enough menu items available for {target_date}. Please contact support.')
            return redirect('meal_pass_dashboard')
    
    # Get available meals (only those configured for this specific date)
    available_meals = []
    configured_meals = [
        daily_options.meal_option_1,
        daily_options.meal_option_2,
        daily_options.meal_option_3,
        daily_options.meal_option_4,
        daily_options.meal_option_5,
    ]
    
    # Check if user has Weekly Premium to show 7 options
    has_weekly_premium = any('Weekly Premium' in sub.meal_pass.name for sub in active_subscriptions)
    
    if has_weekly_premium:
        # For Weekly Premium, show all 5 configured meals plus 2 additional unique meals
        for meal in configured_meals:
            if meal and meal.available:
                meal.savings = meal.price - Decimal('300.00')
                available_meals.append(meal)
        
        # Add 2 more unique meals for Weekly Premium (from remaining full meals)
        all_full_meals = list(MenuItem.objects.filter(category__name='Full Meal', available=True))
        used_meal_ids = [meal.id for meal in available_meals]
        remaining_meals = [meal for meal in all_full_meals if meal.id not in used_meal_ids]
        
        if len(remaining_meals) >= 2:
            additional_meals = random.sample(remaining_meals, 2)
            for meal in additional_meals:
                meal.savings = meal.price - Decimal('300.00')
                available_meals.append(meal)
    else:
        # For other passes, show only the 5 configured meals
        for meal in configured_meals:
            if meal and meal.available:
                meal.savings = meal.price - Decimal('300.00')
                available_meals.append(meal)
    
    # If no meals are configured for this date, show error
    if not available_meals:
        messages.error(request, f'No meals are available for {target_date}. Please contact support.')
        return redirect('meal_pass_dashboard')
    
    # Calculate previous and next dates for navigation
    previous_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)
    
    # Get bulk selection options based on meal pass
    bulk_options = []
    
    # Check existing meal selections for the next 7 days
    from datetime import timedelta
    existing_selections = {}
    for i in range(7):
        check_date = target_date + timedelta(days=i)
        selection = MealPassSelection.objects.filter(
            user=request.user,
            selection_date=check_date
        ).first()
        if selection:
            existing_selections[check_date.strftime('%Y-%m-%d')] = selection.selected_meal.name
    
    # Calculate remaining days
    total_days = 7
    remaining_days = total_days - len(existing_selections)
    
    for subscription in active_subscriptions:
        if 'Weekly Basic' in subscription.meal_pass.name:
            # Weekly Basic only has 7 days option
            if remaining_days > 0:
                bulk_options.append({
                    'days': remaining_days,
                    'label': f'Select for {remaining_days} Remaining Days',
                    'description': f'Pre-order meals for {remaining_days} days (already selected for {len(existing_selections)} days)'
                })
        elif 'Weekly Premium' in subscription.meal_pass.name:
            # Weekly Premium has 7 days option with daily choices
            if remaining_days > 0:
                bulk_options.append({
                    'days': remaining_days,
                    'label': f'Select for {remaining_days} Remaining Days',
                    'description': f'Choose from {remaining_days} different options daily (already selected for {len(existing_selections)} days)'
                })
        elif 'Monthly' in subscription.meal_pass.name:
            # Monthly passes can select 7 days blocks
            if remaining_days > 0:
                bulk_options.append({
                    'days': remaining_days,
                    'label': f'Select for {remaining_days} Remaining Days',
                    'description': f'Pre-order meals for {remaining_days} days (already selected for {len(existing_selections)} days)'
                })
        elif 'Super Special' in subscription.meal_pass.name:
            # Annual passes can select 7 days blocks
            if remaining_days > 0:
                bulk_options.append({
                    'days': remaining_days,
                    'label': f'Select for {remaining_days} Remaining Days',
                    'description': f'Pre-order meals for {remaining_days} days (already selected for {len(existing_selections)} days)'
                })
    
    context = {
        'active_subscriptions': active_subscriptions,
        'selected_subscription': selected_subscription,
        'daily_options': daily_options,
        'available_meals': available_meals,
        'target_date': target_date,
        'today': timezone.now().date(),
        'existing_selection': existing_selection,
        'previous_date': previous_date,
        'next_date': next_date,
        'bulk_options': bulk_options,
        'existing_selections': existing_selections,
        'remaining_days': remaining_days,
    }
    
    return render(request, 'meal_pass/daily_meal_selection.html', context)

@login_required
def select_daily_meal(request):
    """Process daily meal selection (single or bulk)"""
    print(f"DEBUG: select_daily_meal called with method: {request.method}")
    print(f"DEBUG: User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    print(f"DEBUG: POST data: {request.POST}")
    print(f"DEBUG: GET data: {request.GET}")
    
    # Test endpoint to verify routing
    if request.POST.get('test_request'):
        return JsonResponse({'success': True, 'message': 'Test endpoint working'})
    
    if request.method == 'POST':
        try:
            meal_id = request.POST.get('meal_id')
            selection_date = request.POST.get('selection_date')
            bulk_selection = request.POST.get('bulk_selection') == 'true'
            bulk_days = int(request.POST.get('bulk_days', 1))
            bulk_dates = request.POST.get('bulk_dates', '').split(',') if bulk_selection else []
            meal_selections = request.POST.get('meal_selections')
            
            # Debug all received parameters
            print(f"DEBUG: bulk_selection = {bulk_selection}")
            print(f"DEBUG: bulk_days = {bulk_days}")
            print(f"DEBUG: bulk_dates = {bulk_dates}")
            print(f"DEBUG: meal_selections = {meal_selections}")
            print(f"DEBUG: request.POST keys = {list(request.POST.keys())}")
            
            # Handle "Select All 7" functionality
            if meal_selections:
                import json
                selections = json.loads(meal_selections)
                
                print(f"DEBUG: Received {len(selections)} selections")
                print(f"DEBUG: Selections data: {selections}")
                
                selections_created = 0
                selections_skipped = 0
                selections_replaced = 0
                
                # Get user's active subscription once - use stored subscription ID if available
                selected_subscription_id = request.session.get('selected_subscription_id')
                if selected_subscription_id:
                    active_subscription = MealPassSubscription.objects.filter(
                        user=request.user,
                        status='active',
                        end_date__gt=timezone.now(),
                        meals_remaining__gt=0,
                        id=selected_subscription_id
                    ).first()
                    print(f"DEBUG: Using stored subscription ID: {selected_subscription_id}")
                else:
                    # Fall back to first active subscription
                    active_subscription = MealPassSubscription.objects.filter(
                        user=request.user,
                        status='active',
                        end_date__gt=timezone.now(),
                        meals_remaining__gt=0
                    ).first()
                    print(f"DEBUG: No stored subscription ID, using first active subscription")
                
                print(f"DEBUG: Active subscription: {active_subscription}")
                if active_subscription:
                    print(f"DEBUG: Subscription meals remaining: {active_subscription.meals_remaining}")
                    print(f"DEBUG: Subscription is valid: {active_subscription.is_valid()}")
                    print(f"DEBUG: Subscription total meals: {active_subscription.total_meals}")
                    print(f"DEBUG: Subscription status: {active_subscription.status}")
                else:
                    print(f"DEBUG: No active subscription found")
                    return JsonResponse({'success': False, 'message': 'No active meal pass available'})
                
                for i, selection in enumerate(selections):
                    try:
                        # Handle both mealId (old format) and mealName (new format)
                        meal_id = selection.get('mealId')
                        meal_name = selection.get('mealName')
                        date_str = selection['date']
                        bulk_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        
                        print(f"DEBUG: Processing selection {i+1}: meal_id={meal_id}, meal_name={meal_name}, date={date_str}")
                        
                        # Get meal by name (for weekly recipes) or by ID (fallback)
                        if meal_name:
                            # Look up meal by name for weekly recipes
                            meal = MenuItem.objects.filter(name=meal_name, available=True).first()
                            if not meal:
                                print(f"DEBUG: Meal not found with name '{meal_name}'")
                                continue
                        elif meal_id:
                            # Fallback to meal ID lookup
                            meal = MenuItem.objects.filter(id=meal_id).first()
                            if not meal:
                                print(f"DEBUG: Meal not found with id {meal_id}")
                                continue
                        else:
                            print(f"DEBUG: No meal identifier found")
                            continue
                        
                        print(f"DEBUG: Found meal: {meal.name}")
                        
                        # Check if user already selected a meal for this date
                        existing_selection = MealPassSelection.objects.filter(
                            user=request.user,
                            selection_date=bulk_date
                        ).first()
                        
                        if existing_selection:
                            print(f"DEBUG: Found existing selection for {bulk_date}, replacing")
                            # Replace existing selection instead of skipping
                            existing_selection.selected_meal = meal
                            existing_selection.daily_option = DailyMealOption.objects.get(date=bulk_date, is_active=True)
                            existing_selection.save()
                            
                            # IMPORTANT: Use meal from subscription for replaced selections
                            if active_subscription.use_meal():
                                print(f"DEBUG: Successfully used meal for replacement {bulk_date}")
                                print(f"DEBUG: Subscription meals remaining before: {active_subscription.meals_remaining}")
                                print(f"DEBUG: Subscription meals remaining after: {active_subscription.meals_remaining}")
                                selections_replaced += 1
                            else:
                                print(f"DEBUG: Failed to use meal for replacement {bulk_date}")
                                print(f"DEBUG: Subscription meals remaining: {active_subscription.meals_remaining}")
                                continue
                        else:
                            print(f"DEBUG: No existing selection for {bulk_date}, creating new")
                            # Check if user has enough meals remaining
                            if active_subscription.meals_remaining <= 0:
                                print(f"DEBUG: No meals remaining, breaking")
                                break
                            
                            # Get daily options for this date
                            try:
                                daily_options_bulk = DailyMealOption.objects.get(date=bulk_date, is_active=True)
                                print(f"DEBUG: Found daily options for {bulk_date}")
                            except DailyMealOption.DoesNotExist:
                                print(f"DEBUG: No daily options found for date {bulk_date}")
                                continue
                            
                            # Skip all validation - just create the selection
                            print(f"DEBUG: Creating meal selection for {bulk_date}")
                            
                            # Create meal selection for this date
                            meal_selection = MealPassSelection.objects.create(
                                user=request.user,
                                subscription=active_subscription,
                                daily_option=daily_options_bulk,
                                selected_meal=meal,
                                selection_date=bulk_date
                            )
                            
                            print(f"DEBUG: Created meal selection, now using meal")
                            
                            # Use one meal from subscription
                            if active_subscription.use_meal():
                                print(f"DEBUG: Successfully used meal for {bulk_date}")
                                print(f"DEBUG: Subscription meals remaining before: {active_subscription.meals_remaining}")
                                print(f"DEBUG: Subscription meals remaining after: {active_subscription.meals_remaining}")
                                selections_created += 1
                            else:
                                # If use_meal fails, delete the selection and continue
                                print(f"DEBUG: Failed to use meal for date {bulk_date}")
                                print(f"DEBUG: Subscription meals remaining: {active_subscription.meals_remaining}")
                                meal_selection.delete()
                                continue
                        
                    except (ValueError, KeyError) as e:
                        print(f"DEBUG: Error processing selection: {e}")
                        continue
                
                print(f"DEBUG: Final counts: Created={selections_created}, Replaced={selections_replaced}, Skipped={selections_skipped}")
                
                if selections_created > 0 or selections_replaced > 0:
                    message = f'Successfully selected meals for {selections_created} days'
                    if selections_replaced > 0:
                        message += f' and replaced meals for {selections_replaced} days'
                    if selections_skipped > 0:
                        message += f'. Skipped {selections_skipped} days where meals were already selected.'
                    return JsonResponse({'success': True, 'message': message})
                else:
                    print(f"DEBUG: No selections created or replaced")
                    return JsonResponse({'success': False, 'message': 'No meals were selected. Please try again.'})
            
            elif bulk_selection and bulk_days > 1:
                # Handle regular bulk selection for multiple days (same meal)
                selections_created = 0
                selections_skipped = 0
                
                for date_str in bulk_dates:
                    try:
                        bulk_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                        
                        # Get meal and daily options
                        meal = get_object_or_404(MenuItem, id=meal_id)
                        target_date = datetime.strptime(selection_date, '%Y-%m-%d').date()
                        daily_options = get_object_or_404(DailyMealOption, date=target_date, is_active=True)
                        
                        # Validate that this meal is actually configured for this date
                        configured_meals = [
                            daily_options.meal_option_1,
                            daily_options.meal_option_2,
                            daily_options.meal_option_3,
                            daily_options.meal_option_4,
                            daily_options.meal_option_5,
                        ]
                        
                        # Check if the selected meal is one of the configured meals for this date
                        if meal not in configured_meals:
                            return JsonResponse({'success': False, 'message': 'This meal is not available for the selected date'})
                        
                        # Check if the meal is available
                        if not meal.available:
                            return JsonResponse({'success': False, 'message': 'This meal is currently not available'})
                        
                        # Get user's active subscription
                        active_subscription = MealPassSubscription.objects.filter(
                            user=request.user,
                            status='active',
                            end_date__gt=timezone.now(),
                            meals_remaining__gt=0
                        ).first()
                        
                        if not active_subscription:
                            return JsonResponse({'success': False, 'message': 'No active meal pass available'})
                        
                        # Check if user already selected a meal for this date
                        existing_selection = MealPassSelection.objects.filter(
                            user=request.user,
                            selection_date=bulk_date
                        ).first()
                        
                        if existing_selection:
                            selections_skipped += 1
                            continue
                        
                        # Get daily options for this date
                        try:
                            daily_options_bulk = DailyMealOption.objects.get(date=bulk_date, is_active=True)
                        except DailyMealOption.DoesNotExist:
                            continue
                        
                        # Validate meal is available for this date
                        bulk_configured_meals = [
                            daily_options_bulk.meal_option_1,
                            daily_options_bulk.meal_option_2,
                            daily_options_bulk.meal_option_3,
                            daily_options_bulk.meal_option_4,
                            daily_options_bulk.meal_option_5,
                        ]
                        
                        # For Weekly Premium, check if meal is in the 7 available options
                        if 'Weekly Premium' in active_subscription.meal_pass.name:
                            # Get all available meals for this date (7 options for premium)
                            all_full_meals = list(MenuItem.objects.filter(category__name='Full Meal', available=True))
                            used_meal_ids = [m.id for m in bulk_configured_meals if m]
                            remaining_meals = [m for m in all_full_meals if m.id not in used_meal_ids]
                            available_meals = bulk_configured_meals + remaining_meals[:2]
                            
                            if meal not in available_meals:
                                continue
                        else:
                            # For other tiers, check if meal is in the 5 configured meals
                            if meal not in bulk_configured_meals:
                                continue
                        
                        # Create meal selection for this date
                        meal_selection = MealPassSelection.objects.create(
                            user=request.user,
                            subscription=active_subscription,
                            daily_option=daily_options_bulk,
                            selected_meal=meal,
                            selection_date=bulk_date
                        )
                        
                        # Use one meal from subscription
                        if active_subscription.use_meal():
                            selections_created += 1
                        
                    except ValueError:
                        continue
                
                if selections_created > 0:
                    message = f'Successfully selected {meal.name} for {selections_created} days!'
                    if selections_skipped > 0:
                        message += f' Skipped {selections_skipped} days where meals were already selected.'
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': 'No meals were selected. You may have already selected meals for these dates.'})
            
            else:
                # Handle single day selection
                # Get meal and daily options
                meal = get_object_or_404(MenuItem, id=meal_id)
                target_date = datetime.strptime(selection_date, '%Y-%m-%d').date()
                daily_options = get_object_or_404(DailyMealOption, date=target_date, is_active=True)
                
                # Validate that this meal is actually configured for this date
                configured_meals = [
                    daily_options.meal_option_1,
                    daily_options.meal_option_2,
                    daily_options.meal_option_3,
                    daily_options.meal_option_4,
                    daily_options.meal_option_5,
                ]
                
                # Check if the selected meal is one of the configured meals for this date
                if meal not in configured_meals:
                    return JsonResponse({'success': False, 'message': 'This meal is not available for the selected date'})
                
                # Check if the meal is available
                if not meal.available:
                    return JsonResponse({'success': False, 'message': 'This meal is currently not available'})
                
                # Get user's active subscription
                active_subscription = MealPassSubscription.objects.filter(
                    user=request.user,
                    status='active',
                    end_date__gt=timezone.now(),
                    meals_remaining__gt=0
                ).first()
                
                if not active_subscription:
                    return JsonResponse({'success': False, 'message': 'No active meal pass available'})
                
                # Check if user already selected a meal for this date
                existing_selection = MealPassSelection.objects.filter(
                    user=request.user,
                    selection_date=target_date
                ).first()
                
                if existing_selection:
                    return JsonResponse({'success': False, 'message': 'You have already selected a meal for this date'})
                
                # Create meal selection
                meal_selection = MealPassSelection.objects.create(
                    user=request.user,
                    subscription=active_subscription,
                    daily_option=daily_options,
                    selected_meal=meal,
                    selection_date=target_date
                )
                
                # Use one meal from subscription
                if active_subscription.use_meal():
                    return JsonResponse({
                        'success': True,
                        'message': f'Successfully selected {meal.name} for {target_date}!'
                    })
                else:
                    return JsonResponse({'success': False, 'message': 'No meals remaining in your subscription'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
