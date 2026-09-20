from django.shortcuts import render,redirect
from django.contrib import messages
from django.utils import timezone
from mainapp.models import *
from django.db.models import ProtectedError


# Create your views here.
def admindash(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    
    # 1. Base counts
    total_depts = Department.objects.count()
    total_emps = Employee.objects.count()
    total_files = File.objects.count()
    
    # 2. Files by Status
    open_files = File.objects.filter(status='OPEN').count()
    inprogress_files = File.objects.filter(status='IN_PROGRESS').count()
    closed_files = File.objects.filter(status='CLOSED').count()
    
    # 3. Department statistics (number of employees per department)
    from django.db.models import Count
    dept_employees = Department.objects.annotate(emp_count=Count('employee'))
    
    dept_names = [dept.dept_name for dept in dept_employees]
    dept_counts = [dept.emp_count for dept in dept_employees]
    
    # 4. Recent file movements
    recent_movements = FileMovement.objects.select_related('file', 'from_employee', 'to_employee').order_by('-moved_at')[:6]
    
    # 5. Recent files
    recent_files = File.objects.select_related('initiated_by', 'current_holder').order_by('-created_at')[:5]
    
    context = {
        'adminid' : adminid,
        'total_depts' : total_depts,
        'total_emps' : total_emps,
        'total_files' : total_files,
        'open_files' : open_files,
        'inprogress_files' : inprogress_files,
        'closed_files' : closed_files,
        'dept_names' : dept_names,
        'dept_counts' : dept_counts,
        'recent_movements' : recent_movements,
        'recent_files' : recent_files,
    }
    return render(request, "admindash.html", context)

def adminlogout(request):
    if 'adminid' in request.session:
        del request.session['adminid']
        messages.success(request, "Logged out Successfully")
    return redirect('adminlogin')
    
def adddept(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    context = {
        'adminid' : adminid,
    }
    if request.method == "POST":
        dept_name = request.POST.get('dept_name')
        if Department.objects.filter(dept_name=dept_name):
            messages.warning(request,"This department already exits")
            return redirect("adddept")
        dep=Department(dept_name= dept_name)
        dep.save()
        messages.success(request,"Department added successfully")
        return redirect("viewdept")
    return render(request, "adddept.html", context)    



def viewdept(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    depts= Department.objects.all()
    context = {
        'adminid' : adminid,
        'depts' : depts,
    }
    return render(request, "viewdept.html", context)    

def viewemp(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    depts = Department.objects.all()
    emp1 = Employee.objects.all()
    context = {
        'adminid' : adminid,
        'depts' : depts,
        'emp1' : emp1,

    }
    return render(request, "viewemp.html", context)   



 
def addemp(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    depts= Department.objects.all()

    context = {
        'adminid' : adminid,
        'depts' : depts,
    }
    if request.method == "POST":
        empid = request.POST.get('empid')
        name = request.POST.get('name')
        email = request.POST.get('email')
        contactno = request.POST.get('contactno')
        designation= request.POST.get('designation')
        dept_id= request.POST.get('dept_id')
        dept = Department.objects.get(id=dept_id)
        if LoginInfo.objects.filter(username=email):
            messages.warning(request,"This email alredy registered")
            return redirect("addemp")
        log =LoginInfo.objects.create(usertype='employee',username=email,password="12345678",)
        emp=Employee.objects.create(log=log,empid=empid, name=name, email=email,contactno=contactno, designation= designation,department=dept)
        messages.success(request, "Employee added successfully")
        return redirect("viewemp")
    return render(request, "addemp.html", context)    


def changepass(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    
    if request.method == "POST":
        old_pass = request.POST.get('old_pass')
        new_pass = request.POST.get('new_pass')
        confirm_pass = request.POST.get('confirm_pass')
        
        try:
            admin_login = LoginInfo.objects.get(username=adminid, usertype="admin")
        except LoginInfo.DoesNotExist:
            messages.error(request, "Admin account not found")
            return redirect('adminlogin')
            
        if admin_login.password != old_pass:
            messages.error(request, "Old password does not match")
            return redirect('changepass')
            
        if new_pass != confirm_pass:
            messages.error(request, "New password and confirm password do not match")
            return redirect('changepass')
            
        admin_login.password = new_pass
        admin_login.save()
        messages.success(request, "Password changed successfully")
        return redirect('admindash')
        
    context = {
        'adminid' : adminid,
    }
    return render(request, "changepass.html", context) 

def editemp(request, id):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid = request.session.get('adminid')
    try:
        emp = Employee.objects.get(id=id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found")
        return redirect('viewemp')
        
    depts = Department.objects.all()
    
    if request.method == "POST":
        empid = request.POST.get('empid')
        name = request.POST.get('name')
        contactno = request.POST.get('contactno')
        email = request.POST.get('email')
        designation = request.POST.get('designation')
        dept_id = request.POST.get('dept_id')
        
        try:
            dept = Department.objects.get(id=dept_id)
        except Department.DoesNotExist:
            messages.error(request, "Department not found")
            return redirect('viewemp')
            
        if email != emp.email and LoginInfo.objects.filter(username=email).exclude(id=emp.log.id).exists():
            messages.warning(request, "This email already exists")
            return redirect('viewemp')
            
        password = request.POST.get('password')
        if password:
            emp.log.password = password
            
        emp.log.username = email
        emp.log.save()
        
        emp.empid = empid
        emp.name = name
        emp.contactno = contactno
        emp.email = email
        emp.designation = designation
        emp.department = dept
        
        emp.save()
        messages.success(request, "Employee updated successfully")
        return redirect('viewemp')
        
    context = {
        'adminid': adminid,
        'emp': emp,
        'depts': depts,
    }
    return render(request, "editemp.html", context)

def deleteemp(request, id):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    try:
        emp = Employee.objects.get(id=id)
        emp.log.delete() # Deleting LoginInfo will automatically cascade to Employee delete
        messages.success(request, "Employee deleted successfully")
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found")
    except ProtectedError:
        messages.error(request, "Cannot delete employee: they are associated with active or past files/movements.")
    return redirect('viewemp') 

def editdept(request, id):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid = request.session.get('adminid')
    try:
        dept = Department.objects.get(id=id)
    except Department.DoesNotExist:
        messages.error(request, "Department not found")
        return redirect('viewdept')
        
    if request.method == "POST":
        dept_name = request.POST.get('dept_name')
        if Department.objects.filter(dept_name=dept_name).exclude(id=id).exists():
            messages.warning(request, "This department already exists")
            return redirect('viewdept')
            
        dept.dept_name = dept_name
        dept.save()
        messages.success(request, "Department updated successfully")
        return redirect('viewdept')
        
    context = {
        'adminid': adminid,
        'dept': dept,
    }
    return render(request, "editdept.html", context)

def deletedept(request, id):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    try:
        dept = Department.objects.get(id=id)
        if Employee.objects.filter(department=dept).exists():
            messages.error(request, "Cannot delete department: there are employees assigned to this department.")
            return redirect('viewdept')
        dept.delete()
        messages.success(request, "Department deleted successfully")
    except Department.DoesNotExist:
        messages.error(request, "Department not found")
    except ProtectedError:
        messages.error(request, "Cannot delete department: some employees in this department are associated with active or past files.")
    return redirect('viewdept') 

def viewallfiles(request):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid = request.session.get('adminid')
    
    from django.db.models import Prefetch
    movements_prefetch = Prefetch(
        'movements',
        queryset=FileMovement.objects.select_related('from_employee', 'to_employee').order_by('moved_at')
    )
    files = File.objects.select_related('initiated_by', 'current_holder').prefetch_related(movements_prefetch).order_by('-created_at')
    
    context = {
        'adminid': adminid,
        'files': files,
    }
    return render(request, "viewallfiles.html", context) 

def editfile(request, id):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    adminid = request.session.get('adminid')
    try:
        file_obj = File.objects.get(id=id)
    except File.DoesNotExist:
        messages.error(request, "File not found")
        return redirect('viewallfiles')
        
    employees = Employee.objects.all()
    
    if request.method == "POST":
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        holder_id = request.POST.get('current_holder')
        
        try:
            new_holder = Employee.objects.get(id=holder_id)
        except Employee.DoesNotExist:
            messages.error(request, "Employee not found")
            return redirect('viewallfiles')
            
        old_holder = file_obj.current_holder
        
        file_obj.title = title
        file_obj.subject = subject
        file_obj.status = status
        file_obj.priority = priority
        file_obj.current_holder = new_holder
        
        # If admin changed holder, log forward movement
        if old_holder != new_holder:
            FileMovement.objects.create(
                file=file_obj,
                from_employee=old_holder,
                to_employee=new_holder,
                action="FORWARD",
                remarks="Reassigned by Administrator"
            )
            
        # File attachment update (if uploaded)
        attachment_file = request.FILES.get('attachment')
        if attachment_file:
            file_obj.attachment = attachment_file
            
        if status == 'CLOSED':
            file_obj.closed_at = timezone.now()
            FileMovement.objects.create(
                file=file_obj,
                from_employee=new_holder,
                to_employee=None,
                action="CLOSE",
                remarks="Closed by Administrator"
            )
        else:
            file_obj.closed_at = None
            
        file_obj.save()
        messages.success(request, "File updated successfully")
        return redirect('viewallfiles')
        
    context = {
        'adminid': adminid,
        'file': file_obj,
        'employees': employees,
    }
    return render(request, "editfile.html", context)

def deletefile(request, id):
    if 'adminid' not in request.session:
        messages.error(request, "Please login first")
        return redirect('adminlogin')
    try:
        file_obj = File.objects.get(id=id)
        file_obj.delete()
        messages.success(request, "File deleted successfully")
    except File.DoesNotExist:
        messages.error(request, "File not found")
    return redirect('viewallfiles')
