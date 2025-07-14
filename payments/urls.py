# payments/urls.py

from django.urls import path

from . import views


urlpatterns = [
    path('', views.PaymentsPageView.as_view(), name='payments'),
    path('config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session, name="create-checkout-session"),
    path('success/', views.SuccessView.as_view()),
    path('cancelled/', views.CancelledView.as_view()),
    path('checkout/', views.checkout_view, name='checkout'),
    path('webhook/', views.stripe_webhook),
]
