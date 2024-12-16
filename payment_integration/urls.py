from django.urls import path
from .views import initiate_payment, handle_request, payment_start

app_name = "payment_integration"

urlpatterns = [ 
    # Payment APIs
    path('payment_start/', payment_start, name='payment_start'),
    path('initiate-payment/', initiate_payment, name='initiate-payment'),
    path('handle_request/', handle_request, name = 'handle_request'),
]
