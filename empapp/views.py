from django.shortcuts import render,redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Prefetch
from mainapp.models import *


# Create your views here.
def empdash(request):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid=request.session.get('eid')
    
    try:
        emp = Employee.objects.get(email=eid)
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found")
        return redirect('userlogin')
        
    # 1. Employee-specific counts
    # Files initiated by the employee
    initiated_files = File.objects.filter(initiated_by=emp)
    total_initiated = initiated_files.count()
    
    # Files currently holding (pending with employee)
    holding_files = File.objects.filter(current_holder=emp, status__in=['OPEN', 'IN_PROGRESS'])
    total_holding = holding_files.count()
    
    # Closed files initiated by employee
    closed_initiated = initiated_files.filter(status='CLOSED').count()
    
    # Open / In-progress files initiated by employee
    open_initiated = initiated_files.filter(status='OPEN').count()
    inprogress_initiated = initiated_files.filter(status='IN_PROGRESS').count()
    
    # 2. File movements involving this employee
    from django.db.models import Q
    movements = FileMovement.objects.filter(
        Q(from_employee=emp) | Q(to_employee=emp)
    ).select_related('file', 'from_employee', 'to_employee').order_by('-moved_at')[:6]
    
    # Recent files initiated
    recent_initiated = initiated_files.order_by('-created_at')[:5]
    
    context = {
        'eid': eid,
        'emp': emp,
        'total_initiated': total_initiated,
        'total_holding': total_holding,
        'closed_initiated': closed_initiated,
        'open_initiated': open_initiated,
        'inprogress_initiated': inprogress_initiated,
        'movements': movements,
        'holding_files': holding_files[:5],  # top 5 pending files
        'recent_initiated': recent_initiated,
    }
    return render(request, "empdash.html", context)

def emplogout(request):
    if 'eid' in request.session:
        del request.session['eid']
        messages.success(request, "Logged out Successfully")
    return redirect('userlogin')
    
def viewprofile(request):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid=request.session.get('eid')
    emp = Employee.objects.get(email=eid)
    context = {
        'eid': eid,
        'emp' :emp, 
    }
    return render(request, "viewprofile.html", context)

def updateprofile(request):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid=request.session.get('eid')
    emp = Employee.objects.get(email=eid)
    context = {
        'eid': eid,
        'emp' :emp, 
        
    }
    if request.method == "POST":
        name = request.POST.get("name")
        contactno = request.POST.get("contactno")
        picture = request.FILES.get("picture")
        address = request.POST.get("address")
        emp.name=name
        emp.contactno=contactno
        if picture:
            emp.picture=picture
        emp.address=address
        emp.save()
        messages.success(request, "Profile Updated Successfully")
        return redirect('viewprofile')
    return render(request, "updateprofile.html", context)

def initiatefile(request):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found")
        return redirect('userlogin')
        
    departments = Department.objects.all()
    employees = Employee.objects.exclude(id=emp.id)
    
    if request.method == "POST":
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        priority = request.POST.get('priority')
        attachment = request.FILES.get('attachment')
        remarks = request.POST.get('remarks', '')
        
        target_emp_id = request.POST.get('emp_id')
        
        try:
            target_emp = Employee.objects.get(id=target_emp_id)
        except Employee.DoesNotExist:
            target_emp = emp  # keep with self if not specified
            
        file_obj = File.objects.create(
            title=title,
            subject=subject,
            initiated_by=emp,
            current_holder=target_emp,
            priority=priority,
            attachment=attachment,
            status="OPEN"
        )
        
        # Log CREATE action
        FileMovement.objects.create(
            file=file_obj,
            from_employee=emp,
            to_employee=target_emp,
            action="CREATE",
            remarks=remarks if remarks else "File Initiated"
        )
        
        messages.success(request, f"File {file_obj.file_no} initiated successfully!")
        return redirect('viewfiles')
        
    context = {
        'eid': eid,
        'emp': emp,
        'departments': departments,
        'employees': employees,
    }
    return render(request, "initiatefile.html", context)

def viewfiles(request):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found")
        return redirect('userlogin')
        
    # 1. Pending Actions Queue (holding files)
    pending_files = File.objects.filter(current_holder=emp).exclude(status="CLOSED")
    
    # 2. Received Files (holding files where current_holder = emp, but initiated_by != emp)
    received_files = pending_files.exclude(initiated_by=emp)
    
    # 3. Initiated Files
    initiated_files = File.objects.filter(initiated_by=emp)
    
    # 4. Handled Files History
    movements_prefetch = Prefetch(
        'movements',
        queryset=FileMovement.objects.select_related('from_employee', 'to_employee').order_by('moved_at')
    )
    handled_files = File.objects.filter(
        Q(initiated_by=emp) | Q(movements__from_employee=emp) | Q(movements__to_employee=emp)
    ).distinct().prefetch_related(movements_prefetch).order_by('-created_at')
    
    context = {
        'eid': eid,
        'emp': emp,
        'pending_files': pending_files,
        'received_files': received_files,
        'initiated_files': initiated_files,
        'handled_files': handled_files,
    }
    return render(request, "viewfiles.html", context)

def emp_editfile(request, id):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
        file_obj = File.objects.get(id=id)
    except (Employee.DoesNotExist, File.DoesNotExist):
        messages.error(request, "Resource not found")
        return redirect('viewfiles')
        
    # Check permissions
    if file_obj.current_holder != emp and file_obj.initiated_by != emp:
        messages.error(request, "Unauthorized to edit this file")
        return redirect('viewfiles')
        
    if request.method == "POST":
        file_obj.title = request.POST.get('title')
        file_obj.subject = request.POST.get('subject')
        file_obj.priority = request.POST.get('priority')
        
        attachment_file = request.FILES.get('attachment')
        if attachment_file:
            file_obj.attachment = attachment_file
            
        file_obj.save()
        messages.success(request, "File updated successfully!")
        return redirect('viewfiles')
        
    context = {
        'eid': eid,
        'emp': emp,
        'file': file_obj,
    }
    return render(request, "emp_editfile.html", context)

def emp_deletefile(request, id):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
        file_obj = File.objects.get(id=id)
    except (Employee.DoesNotExist, File.DoesNotExist):
        messages.error(request, "Resource not found")
        return redirect('viewfiles')
        
    # Check permissions: only initiator can delete
    if file_obj.initiated_by != emp:
        messages.error(request, "Only the file initiator can delete it")
        return redirect('viewfiles')
        
    file_obj.delete()
    messages.success(request, "File deleted successfully!")
    return redirect('viewfiles')

def forwardfile(request, id):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
        file_obj = File.objects.get(id=id)
    except (Employee.DoesNotExist, File.DoesNotExist):
        messages.error(request, "Resource not found")
        return redirect('viewfiles')
        
    if file_obj.current_holder != emp or file_obj.status == "CLOSED":
        messages.error(request, "You cannot forward this file")
        return redirect('viewfiles')
        
    departments = Department.objects.all()
    employees = Employee.objects.exclude(id=emp.id)
    
    if request.method == "POST":
        target_emp_id = request.POST.get('emp_id')
        remarks = request.POST.get('remarks', '')
        
        try:
            target_emp = Employee.objects.get(id=target_emp_id)
        except Employee.DoesNotExist:
            messages.error(request, "Invalid employee selected")
            return redirect('viewfiles')
            
        file_obj.current_holder = target_emp
        if file_obj.status == "OPEN":
            file_obj.status = "IN_PROGRESS"
        file_obj.save()
        
        FileMovement.objects.create(
            file=file_obj,
            from_employee=emp,
            to_employee=target_emp,
            action="FORWARD",
            remarks=remarks if remarks else "Forwarded"
        )
        
        messages.success(request, f"File {file_obj.file_no} forwarded to {target_emp.name}!")
        return redirect('viewfiles')
        
    context = {
        'eid': eid,
        'emp': emp,
        'file': file_obj,
        'departments': departments,
        'employees': employees,
    }
    return render(request, "forwardfile.html", context)

def returnfile(request, id):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
        file_obj = File.objects.get(id=id)
    except (Employee.DoesNotExist, File.DoesNotExist):
        messages.error(request, "Resource not found")
        return redirect('viewfiles')
        
    if file_obj.current_holder != emp or file_obj.status == "CLOSED":
        messages.error(request, "You cannot return this file")
        return redirect('viewfiles')
        
    # Find previous holder
    last_movement = FileMovement.objects.filter(file=file_obj, to_employee=emp).order_by('-moved_at').first()
    if last_movement and last_movement.from_employee and last_movement.from_employee != emp:
        target_emp = last_movement.from_employee
    else:
        target_emp = file_obj.initiated_by
        
    if target_emp == emp:
        messages.error(request, "You cannot return a file to yourself.")
        return redirect('viewfiles')
        
    if request.method == "POST":
        remarks = request.POST.get('remarks', '')
        
        file_obj.current_holder = target_emp
        file_obj.save()
        
        FileMovement.objects.create(
            file=file_obj,
            from_employee=emp,
            to_employee=target_emp,
            action="RETURN",
            remarks=remarks if remarks else "Returned"
        )
        
        messages.success(request, f"File {file_obj.file_no} returned to {target_emp.name}!")
        return redirect('viewfiles')
        
    context = {
        'eid': eid,
        'emp': emp,
        'file': file_obj,
        'target_emp': target_emp,
    }
    return render(request, "returnfile.html", context)

def closefile(request, id):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
        file_obj = File.objects.get(id=id)
    except (Employee.DoesNotExist, File.DoesNotExist):
        messages.error(request, "Resource not found")
        return redirect('viewfiles')
        
    # Check permission: Only the initiator of the file can close it
    if file_obj.initiated_by != emp:
        messages.error(request, "Only the file initiator can close it")
        return redirect('viewfiles')
        
    if file_obj.status == "CLOSED":
        messages.error(request, "This file is already closed")
        return redirect('viewfiles')
        
    if request.method == "POST":
        remarks = request.POST.get('remarks', '')
        
        file_obj.status = "CLOSED"
        file_obj.closed_at = timezone.now()
        file_obj.save()
        
        FileMovement.objects.create(
            file=file_obj,
            from_employee=emp,
            to_employee=None,
            action="CLOSE",
            remarks=remarks if remarks else "Closed"
        )
        
        messages.success(request, f"File {file_obj.file_no} closed successfully!")
        return redirect('viewfiles')
        
    context = {
        'eid': eid,
        'emp': emp,
        'file': file_obj,
    }
    return render(request, "closefile.html", context)

def emp_changepass(request):
    if 'eid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('userlogin')
    eid = request.session.get('eid')
    try:
        emp = Employee.objects.get(email=eid)
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found")
        return redirect('userlogin')
        
    if request.method == "POST":
        old_pass = request.POST.get('old_pass')
        new_pass = request.POST.get('new_pass')
        confirm_pass = request.POST.get('confirm_pass')
        
        log_info = emp.log
        if log_info.password != old_pass:
            messages.error(request, "Old password does not match")
            return redirect('emp_changepass')
            
        if new_pass != confirm_pass:
            messages.error(request, "New password and confirm password do not match")
            return redirect('emp_changepass')
            
        log_info.password = new_pass
        log_info.save()
        messages.success(request, "Password changed successfully")
        return redirect('empdash')
        
    context = {
        'eid': eid,
        'emp': emp,
    }
    return render(request, "emp_changepass.html", context)

