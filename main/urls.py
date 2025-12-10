from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_us, name='about'),
    path('menu/', views.menu_page, name='menu'),

    path('cart/', views.cart_page, name='cart'),
    path('cart/add/<int:food_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:food_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:food_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/feedback-reports/', views.feedback_reports, name='feedback_reports'),
    path('employee/order-reports/', views.order_reports, name='order_reports'),
    path('unauthorized/', views.unauthorized, name='unauthorized'),

    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),

    path('employee/food/add/', views.add_food, name='add_food'),
    path('employee/food/edit/<int:food_id>/', views.edit_food, name='edit_food'),
    path('employee/food/delete/<int:food_id>/', views.delete_food, name='delete_food'),

    path('employee/order-reports/download/', views.download_order_report, name='download_order_report'),
    path('employee/feedback-reports/download/', views.download_feedback_report, name='download_feedback_report'),

    path('employee/order/update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),

    path('order-success/', views.order_success, name='order_success'),

    path('employee/order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('employee/feedback/delete/<int:feedback_id>/', views.delete_feedback, name='delete_feedback'),


]
