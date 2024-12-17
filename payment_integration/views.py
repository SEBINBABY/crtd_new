from django.shortcuts import render
import razorpay
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
from django.contrib.auth.decorators import login_required

# Payment integration starts from here 
@login_required
def payment_start(request):
    user = request.user
    if user.is_user:
        full_name = user.username
        email = user.email
    context = {
        "full_name":full_name,
        "email":email
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
            contact_number =user.contact_number
        print(f"Fullname:{full_name}, email:{email}, contact:{contact_number}")
        callback_url = "http://127.0.0.1:8000//handle_request/"
        if not settings.DEBUG:  # If live mode
            callback_url = "http://3.109.183.125:8000/handle_request/"
        notes = {"order-type":"basic order from the website"}
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        # payment_obj = Payment.objects.get(user=user)
        # amount = payment_obj.amount
        amount = 1.0
        razorpay_order = client.order.create({
            "amount": amount*100,  # Amount in paise (1.00 INR)
            "currency": "INR",
            "payment_capture": 1,  # Auto-capture payment
            "notes":notes,
        })
        razorpay_order_id = razorpay_order['id']
        # Save the order details in the database
        Payment.objects.create(
            user=user,
            razorpay_order_id=razorpay_order_id,
            amount=amount,  # Convert paise to INR
            status='pending'
        )
        context = {
            "razorpay_order_id":razorpay_order_id,
            "amount":amount,  # Amount in INR
            "full_name":full_name,
            "email":email,
            "contact_number":contact_number,
            "razorpay_merchant_id":settings.RAZORPAY_KEY_ID,
            "callback_url":callback_url
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
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_payment_id = request.POST.get("razorpay_payment_id")
            razorpay_order_id = request.POST.get("razorpay_order_id")
            razorpay_signature = request.POST.get("razorpay_signature")
            print("Payment ID:", razorpay_payment_id)
            print("Order ID:", razorpay_order_id)
            print("Signature:", razorpay_signature)

            # Verify the signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            try:
                payment_obj = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            except Exception as e:
                print(f"Error: {e}")  # Log the error
                return JsonResponse({"status": "error", "message": str(e)})
            payment_obj.razorpay_payment_id = razorpay_payment_id
            payment_obj.razorpay_signature = razorpay_signature
            payment_obj.save()
            result = client.utility.verify_payment_signature(params_dict)
            print("Signature verification result:", result)  # Log the verification result
            if result is None:
                amount = payment_obj.amount * 100  # We have to pass in paisa
                try:
                    client.payment.capture(razorpay_payment_id, amount)
                    print("Payment captured successfully.")
                    payment_obj.status = "successful"
                    payment_obj.save()
                    request.user.has_paid = True
                    request.user.save()
                    return render(request, "payment_success.html")
                except razorpay.errors.RazorpayError as e:
                    # Log the error returned by Razorpay for Invalid signature
                    print(f"Payment capture failed: {e}")
                    payment_obj.status = "failed"
                    payment_obj.save()
                    return render(request, "payment_fail.html", {"error": f"Payment capture failed: {e}"})        
        except Exception as e:
            print(f"Error: {e}")  # Log the error
            return JsonResponse({"status": "error", "message": str(e)})
    # For non-POST requests, return a 405 Method Not Allowed response
    return JsonResponse({"status": "error", "message": "Method Not Allowed"}, status=405)


