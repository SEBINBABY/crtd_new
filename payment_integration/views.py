from django.shortcuts import render
import razorpay
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from .models import Payment
from django.contrib.auth.decorators import login_required
from admin_dashboard.models import User
from admin_dashboard.models import Amount

# Initialize Razorpay client globally
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Payment integration starts from here
@never_cache
@login_required
def payment_start(request):
    user = request.user
    if user.is_user:
        full_name = user.username
        email = user.email
    context = {
        "full_name": full_name,
        "email": email
    }
    return render(request, "payment-start.html", context)

@csrf_exempt
def initiate_payment(request):
    try:
        # Fetch user information from the session
        user = request.user
        if user.is_user:
            full_name = user.username
            email = user.email
            contact_number = user.contact_number
        print(f"Fullname:{full_name}, email:{email}, contact:{contact_number}")
        callback_url = "http://3.109.183.125:8000/handle_request/"
        if not settings.DEBUG:  # If live mode
            callback_url = "http://3.109.183.125:8000/handle_request/"
        notes = {"order-type": "basic order from the website"}
        
        try:
            amount_obj = Amount.objects.first()  # Get the first record (assuming one record exists)
            amount = amount_obj.value  # Assuming 'amount' is the field in the Amount model
        except Amount.DoesNotExist:
            # Handle the case where the amount doesn't exist (e.g., set a default amount or throw an error)
            amount = 1.0  # default amount, can be adjusted based on our needs

        razorpay_order = client.order.create({
            "amount": amount * 100,  # Amount in paise (1.00 INR)
            "currency": "INR",
            "payment_capture": 1,  # Auto-capture payment
            "notes": notes,
        })
        razorpay_order_id = razorpay_order['id']

        # Check if the Razorpay order ID already exists in the database
        existing_order = Payment.objects.filter(razorpay_order_id=razorpay_order_id).exists()
        if existing_order:
            print(f"Order ID {razorpay_order_id} already exists in the database.")
            return JsonResponse({
                "status": "error",
                "message": "Duplicate order ID detected. Please try again."
            })

        # Save the order details in the database
        Payment.objects.create(
            user=user,
            razorpay_order_id=razorpay_order_id,
            amount=amount,  # Convert paise to INR
            status='pending'
        )
        context = {
            "razorpay_order_id": razorpay_order_id,
            "amount": amount,  # Amount in INR
            "full_name": full_name,
            "email": email,
            "contact_number": contact_number,
            "razorpay_merchant_id": settings.RAZORPAY_KEY_ID,
            "callback_url": callback_url
        }
        return render(request, "payment-second.html", context)
    except Exception as e:
        print(f"Error: {e}")  # Log the error
        return JsonResponse({"status": "error", "message": str(e)})

# Payment Confirmation Endpoint: This endpoint will verify the payment signature from Razorpay after payment
@csrf_exempt
def handle_request(request):
    print(f"Request Method: {request.method}")  # Log the request method
    if request.method == "POST":
        try:
            # Log the entire request body to debug missing parameters
            print(f"Request Data: {request.POST}")

            razorpay_payment_id = request.POST.get("razorpay_payment_id")
            razorpay_order_id = request.POST.get("razorpay_order_id")
            razorpay_signature = request.POST.get("razorpay_signature")

            # Log the extracted values
            print(f"Order ID: {razorpay_order_id}")
            print(f"Signature: {razorpay_signature}")
            print(f"payment_id: {razorpay_payment_id}")

            if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
                return JsonResponse({"status": "error", "message": "Missing parameters in the request."})

            # Verify the signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            try:
                payment_obj = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                print(f"Found Payment object: {payment_obj}")
            except Payment.DoesNotExist:
                print(f"Payment matching query does not exist for order_id {razorpay_order_id}")
                return JsonResponse({"status": "error", "message": "Payment record not found."})

            # Log the current status of the order
            print(f"Order {razorpay_order_id} current status: {payment_obj.status}")

            # Handle the case where the payment has already been processed
            if payment_obj.status == "successful":
                print(f"Payment already successful for order_id {razorpay_order_id}")
                return JsonResponse({
                    "status": "error",
                    "message": "Your payment has already been processed."
                })

            # Save payment details to the object
            payment_obj.razorpay_payment_id = razorpay_payment_id
            payment_obj.razorpay_signature = razorpay_signature
            payment_obj.save()

            # Verify payment signature using Razorpay utility
            result = client.utility.verify_payment_signature(params_dict)
            print("Signature verification result:", result)  # Log the verification result

            # Check if the signature is valid
            if result is False:
                payment_obj.status = "failed"
                payment_obj.save()
                # Render the payment failure page if verification fails
                return render(request, "payment_fail.html", {"order_id": razorpay_order_id, "message": "Signature verification failed."})

            # The payment was already captured automatically by Razorpay
            payment_obj.status = "successful"
            payment_obj.save()

            # Update the user model to reflect the paid status
            user = request.user
            email = user.email
            print('User email:', email)
            user = User.objects.get(email=email)
            user.has_paid = True
            user.save()
            print("User paid status:", user.has_paid)

            # If payment is successful, render the success page
            return render(request, "payment_success.html")

        except Exception as e:
            print(f"Error: {e}")  # Log the error
            return JsonResponse({"status": "error", "message": str(e)})

    # For non-POST requests, return a 405 Method Not Allowed response
    return JsonResponse({"status": "error", "message": "Method Not Allowed"}, status=405)
