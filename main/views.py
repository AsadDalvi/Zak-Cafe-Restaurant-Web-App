from django.shortcuts import render, redirect, get_object_or_404
from .forms import FeedbackForm, CheckoutForm, CustomerProfileForm
from .models import Food, Order, OrderItem, Feedback
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import csv
from django.http import HttpResponse
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

# Home
def home(request):
    return render(request, 'htmls/home.html')

# About us
def about_us(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Feedback submitted successfully!")
            return redirect('about')
    else:
        form = FeedbackForm()
    return render(request, 'htmls/about.html', {'form': form})

# Menu
def menu_page(request):
    foods = Food.objects.all()
    return render(request, 'htmls/menu.html', {'foods': foods})

# Cart
def cart_page(request):
    cart = request.session.get('cart', {})
    cart_items, total_price = [], 0
    for food_id, qty in cart.items():
        try:
            food = Food.objects.get(id=food_id)
            item_total = food.price * qty
            total_price += item_total
            cart_items.append({'food': food, 'quantity': qty, 'total': item_total})
        except Food.DoesNotExist:
            pass
    return render(request, 'htmls/cart.html', {'cart_items': cart_items, 'total_price': total_price})

def add_to_cart(request, food_id):
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[str(food_id)] = cart.get(str(food_id), 0) + qty
        request.session['cart'] = cart
    return redirect('cart')

def update_cart(request, food_id):
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        if qty > 0:
            cart[str(food_id)] = qty
        else:
            cart.pop(str(food_id), None)
        request.session['cart'] = cart
    return redirect('cart')

def remove_from_cart(request, food_id):
    cart = request.session.get('cart', {})
    cart.pop(str(food_id), None)
    request.session['cart'] = cart
    return redirect('cart')



def order_success(request):
    return render(request, 'htmls/order_success.html')

# Checkout
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('menu')

    cart_items, total_price = [], Decimal('0.00')
    for food_id, qty in cart.items():
        try:
            food = Food.objects.get(id=food_id)
            total_price += food.price * qty
            cart_items.append({'food': food, 'quantity': qty, 'total': food.price * qty})
        except Food.DoesNotExist:
            pass

    delivery_charge = Decimal('0.500')
    grand_total = total_price + delivery_charge

    selected_payment = 'cod'  # default selected

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        selected_payment = request.POST.get('payment_method', 'cod')
        if form.is_valid():
            if selected_payment == 'cod':
                order = Order.objects.create(
                    customer=request.user if request.user.is_authenticated else None,
                    name=form.cleaned_data['name'],
                    phone=form.cleaned_data['phone'],
                    address=form.cleaned_data['address'],
                    total_price=grand_total,
                    payment_method='Cash on Delivery'
                )
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        food=item['food'],
                        quantity=item['quantity'],
                        price=item['food'].price
                    )
                request.session['cart'] = {}
                messages.success(request, "Order placed successfully! Payment: Cash on Delivery.")
                return redirect('order_success')
            else:
                messages.error(request, "Card payment is currently unavailable. Please select Cash on Delivery.")
    else:
        form = CheckoutForm()

    return render(request, 'htmls/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'selected_payment': selected_payment
    })




# Registration
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')
        user = User.objects.create_user(username=username, email=email, password=password)
        customer_group = Group.objects.get(name='Customer')
        user.groups.add(customer_group)
        messages.success(request, "Account created successfully! You can login now.")
        return redirect('login')
    return render(request, 'htmls/register.html')

# Login / Logout
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect('home')
        messages.error(request, "Invalid username or password")
        return redirect('login')
    return render(request, 'htmls/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# Employee checks
def employee_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return redirect('unauthorized')
    return wrapper

def employee_check(user):
    return user.is_authenticated and user.is_staff

# Unauthorized
def unauthorized(request):
    return render(request, 'htmls/unauthorized.html')


# Dashboards
@login_required
@user_passes_test(employee_check)
def employee_dashboard(request):
    foods = Food.objects.all()
    
    # Filters
    order_filter = request.GET.get('order_filter', 'all')  # '24h', '3d', '1w', '1m', 'pending', 'all'
    feedback_filter = request.GET.get('feedback_filter', 'all')  # '24h', '3d', '1w', '1m', 'all'
    
    now = timezone.now()
    
    # Orders
    orders = Order.objects.all().order_by('-created_at')
    
    if order_filter == '24h':
        orders = orders.filter(created_at__gte=now - timedelta(hours=24))
    elif order_filter == '3d':
        orders = orders.filter(created_at__gte=now - timedelta(days=3))
    elif order_filter == '1w':
        orders = orders.filter(created_at__gte=now - timedelta(weeks=1))
    elif order_filter == '1m':
        orders = orders.filter(created_at__gte=now - timedelta(days=30))
    elif order_filter == 'pending':
        orders = orders.filter(status='Pending')
    
    # Total revenue from completed orders
    total_received = orders.filter(status='Completed').aggregate(total=Sum('total_price'))['total'] or 0
    
    # Feedbacks
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    
    if feedback_filter == '24h':
        feedbacks = feedbacks.filter(submitted_at__gte=now - timedelta(hours=24))
    elif feedback_filter == '3d':
        feedbacks = feedbacks.filter(submitted_at__gte=now - timedelta(days=3))
    elif feedback_filter == '1w':
        feedbacks = feedbacks.filter(submitted_at__gte=now - timedelta(weeks=1))
    elif feedback_filter == '1m':
        feedbacks = feedbacks.filter(submitted_at__gte=now - timedelta(days=30))
    
    context = {
        'foods': foods,
        'orders': orders,
        'feedbacks': feedbacks,
        'total_received': total_received,
        'order_filter': order_filter,
        'feedback_filter': feedback_filter
    }
    
    return render(request, 'htmls/employee_dashboard.html', context)



@login_required
@user_passes_test(employee_check)
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, "Order deleted successfully.")
    return redirect('employee_dashboard')


@login_required
@user_passes_test(employee_check)
def delete_feedback(request, feedback_id):
    fb = get_object_or_404(Feedback, id=feedback_id)
    fb.delete()
    messages.success(request, "Feedback deleted successfully.")
    return redirect('employee_dashboard')




@login_required
def customer_dashboard(request):
    user = request.user
    orders = Order.objects.filter(customer=user).order_by('-created_at')
    # Feedback does not have customer FK; show all or filter by email
    feedbacks = Feedback.objects.filter(email=user.email).order_by('-submitted_at')
    form = CustomerProfileForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('customer_dashboard')
    return render(request, 'htmls/customer_dashboard.html', {'orders': orders, 'feedbacks': feedbacks, 'form': form})



# Reports
@login_required
@user_passes_test(lambda u: u.is_staff)
def order_reports(request):
    orders = Order.objects.all().order_by('-created_at')

    # CSV download
    if request.GET.get('download') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="order_reports.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer', 'Total Price (OMR)', 'Status', 'Date'])

        for order in orders:
            # Ensure safe datetime formatting
            order_date = order.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "N/A"
            customer_name = order.customer.username if order.customer else "Guest"

            writer.writerow([
                str(order.id),
                str(customer_name),
                str(order.total_price),
                str(order.status),
                order_date
            ])
        return response

    # Render template if not downloading CSV
    return render(request, 'htmls/order_reports.html', {'orders': orders})




@login_required
@user_passes_test(employee_check)
def feedback_reports(request):
    feedback_list = Feedback.objects.all().order_by('-submitted_at')

    # CSV download
    if request.GET.get('download') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="feedback_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Message', 'Date Submitted'])

        for feedback in feedback_list:
            writer.writerow([feedback.name, feedback.email, feedback.message, feedback.submitted_at])

        return response

    return render(request, 'htmls/feedback_reports.html', {'feedback_list': feedback_list})




# Employee Food Management Views
@login_required
@user_passes_test(employee_check)
def add_food(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        Food.objects.create(name=name, price=price, image=image)
        messages.success(request, "Food item added successfully!")
        return redirect('employee_dashboard')
    return render(request, 'htmls/add_food.html')


@login_required
@user_passes_test(employee_check)
def edit_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    if request.method == 'POST':
        food.name = request.POST.get('name')
        food.price = request.POST.get('price')
        if request.FILES.get('image'):
            food.image = request.FILES.get('image')
        food.save()
        messages.success(request, "Food item updated successfully!")
        return redirect('employee_dashboard')
    return render(request, 'htmls/edit_food.html', {'food': food})


@login_required
@user_passes_test(employee_check)
def delete_food(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    food.delete()
    messages.success(request, "Food item deleted successfully!")
    return redirect('employee_dashboard')


# Download Order Report as CSV
@login_required
@user_passes_test(employee_check)
def download_order_report(request):
    orders = Order.objects.all().order_by('-created_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="order_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Total Price', 'Status', 'Placed On'])

    for order in orders:
        customer_name = order.customer.username if order.customer else order.name
        writer.writerow([order.id, customer_name, order.total_price, order.status, order.created_at])

    return response


# Download Feedback Report as CSV
@login_required
@user_passes_test(employee_check)
def download_feedback_report(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="feedback_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Message', 'Submitted At'])

    for fb in feedbacks:
        writer.writerow([fb.name, fb.email, fb.message, fb.submitted_at])

    return response


@login_required
@user_passes_test(employee_check)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Completed', 'Cancelled']:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to {new_status}.")
    return redirect('employee_dashboard')



