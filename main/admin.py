from django.contrib import admin
from .models import Food, Order, OrderItem, Feedback
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Food admin
@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'image')  # Show these columns in the admin list
    search_fields = ('name',)                  # Search bar for food names
    list_filter = ('price',)                   # Filter sidebar by price

# Inline for OrderItem (used if needed in OrderAdmin)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Order admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_price', 'created_at', 'status')
    list_filter = ('created_at', 'status')
    search_fields = ('customer__username', 'name', 'phone', 'address')
    inlines = [OrderItemInline]  # Shows order items inline

# Register OrderItem separately if you want to manage them individually
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'food', 'quantity', 'price')
    search_fields = ('food__name', 'order__name')

# Feedback admin
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'submitted_at')
    list_filter = ('submitted_at',)
    search_fields = ('name', 'email', 'message')

# Extend UserAdmin to show staff/employee status
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
