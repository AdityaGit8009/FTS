from django.shortcuts import render,redirect
from.models import LoginInfo, Employee
from django.contrib import messages
import random
from django.core.mail import send_mail
from django.utils import timezone


# Create your views here.
def index(request):
        return render(request, "index.html")
def contact(request):
        return render(request, "contact.html")
def adminlogin(request):
        if request.method == "POST":
                username = request.POST.get('username')
                password = request.POST.get('password')
                try:
                        admin=LoginInfo.objects.get(username=username,password=password,usertype="admin")
                        if admin is not None:
                                messages.success(request, "welcome Admin")
                                request.session['adminid']=admin.username
                                return redirect('admindash')
                        pass
                except LoginInfo.DoesNotExist:
                        messages.warning(request, "Invailid username or password")
                        return redirect('adminlogin')
        return render(request, "adminlogin.html")

def userlogin(request):
        if request.method == "POST":
                        username = request.POST.get('username')
                        password = request.POST.get('password')
                        try:
                                emp=LoginInfo.objects.get(username=username,password=password,usertype="employee")
                                if emp is not None:
                                        messages.success(request, "welcome Employee")
                                        request.session['eid']=emp.username
                                        return redirect('empdash')
                                pass
                        except LoginInfo.DoesNotExist:
                                messages.warning(request, "Invailid username or password")
                                return redirect('userlogin')
        return render(request, "userlogin.html")

def forgot_password(request):
    if request.GET.get('action') == 'cancel':
        if 'reset_email' in request.session: del request.session['reset_email']
        if 'otp' in request.session: del request.session['otp']
        if 'otp_time' in request.session: del request.session['otp_time']
        return redirect('userlogin')
        
    email = request.session.get('reset_email')
    
    if request.method == "POST":
        # STEP 1: Enter email and send OTP
        if not email:
            email_input = request.POST.get('email')
            try:
                emp = Employee.objects.get(email=email_input)
                # Generate OTP
                otp = str(random.randint(100000, 999999))
                request.session['reset_email'] = email_input
                request.session['otp'] = otp
                request.session['otp_time'] = timezone.now().timestamp()
                
                # Send email with OTP
                subject = "FTS - Password Reset OTP"
                message = f"Hello {emp.name},\n\nYour OTP for password reset is: {otp}.\nIt is valid for 5 minutes.\n\nRegards,\nGreen Gas FTS Team"
                send_mail(
                    subject,
                    message,
                    'no-reply@fts.com',
                    [email_input],
                    fail_silently=False,
                )
                
                messages.success(request, f"OTP has been sent to your email {email_input}.")
                return redirect('forgot_password')
            except Employee.DoesNotExist:
                messages.error(request, "This email is not registered with any employee.")
                return redirect('forgot_password')
                
        # STEP 2: Verify OTP
        else:
            if 'resend' in request.POST:
                # Handle resending OTP
                try:
                    emp = Employee.objects.get(email=email)
                    otp = str(random.randint(100000, 999999))
                    request.session['otp'] = otp
                    request.session['otp_time'] = timezone.now().timestamp()
                    
                    send_mail(
                        "FTS - Password Reset OTP",
                        f"Hello {emp.name},\n\nYour OTP for password reset is: {otp}.\nIt is valid for 5 minutes.\n\nRegards,\nGreen Gas FTS Team",
                        'no-reply@fts.com',
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, "OTP has been resent successfully.")
                except Employee.DoesNotExist:
                    messages.error(request, "Employee details not found.")
                return redirect('forgot_password')
                
            otp_input = request.POST.get('otp')
            session_otp = request.session.get('otp')
            otp_time = request.session.get('otp_time')
            
            # Check expiry (5 minutes = 300 seconds)
            if not otp_time or (timezone.now().timestamp() - otp_time) > 300:
                messages.error(request, "OTP has expired. Please request a new one.")
                if 'otp' in request.session: del request.session['otp']
                if 'otp_time' in request.session: del request.session['otp_time']
                return redirect('forgot_password')
                
            if otp_input == session_otp:
                # OTP is correct! Reset password to '12345678'
                try:
                    emp = Employee.objects.get(email=email)
                    log_info = emp.log
                    log_info.password = "12345678"
                    log_info.save()
                    
                    # Send confirmation email with new password
                    send_mail(
                        "FTS - Password Reset Success",
                        f"Hello {emp.name},\n\nYour password has been successfully reset.\nYour new default password is: 12345678\n\nPlease login and change your password immediately.\n\nRegards,\nGreen Gas FTS Team",
                        'no-reply@fts.com',
                        [email],
                        fail_silently=False,
                    )
                    
                    messages.success(request, "Verification successful! Your password has been reset to '12345678' and sent to your email.")
                    
                    # Clear session keys
                    del request.session['reset_email']
                    del request.session['otp']
                    del request.session['otp_time']
                    
                    return redirect('userlogin')
                except Employee.DoesNotExist:
                    messages.error(request, "Employee account not found.")
                    return redirect('forgot_password')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect('forgot_password')
                
    # GET request
    context = {
        'step_verify': bool(email),
        'email': email,
    }
    return render(request, "forgot_password.html", context)


 