from django.db import models
from django.utils import timezone

# Create your models here.
class LoginInfo(models.Model):
    id=models.BigAutoField(primary_key=True)
    usertype= models.CharField(max_length=20)
    username=models.CharField(max_length=100,unique=True)
    password=models.CharField(max_length=256)
    
    def __str__(self):
            return f"{self.usertype} - {self.username}"
    
class Department(models.Model):
    dept_name=models.CharField(max_length=100,unique=True)

class Employee(models.Model):
    log = models.OneToOneField(LoginInfo,on_delete=models.CASCADE)
    empid = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    contactno = models.CharField(max_length=15)
    email = models.CharField(max_length=50)
    designation = models.CharField(max_length=50)
    department = models.ForeignKey(Department,on_delete=models.CASCADE)
    picture = models.ImageField(upload_to="profiles",null=True,blank=True)
    address = models.TextField()


class File(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("CLOSED", "Closed"),
    ]
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    ]
    file_no = models.CharField(max_length=30, unique=True, editable=False)
    title = models.CharField(max_length=200)
    subject = models.TextField(blank=True)
    initiated_by = models.ForeignKey(Employee,on_delete=models.PROTECT,related_name="initiated_files")
    current_holder = models.ForeignKey(Employee,on_delete=models.PROTECT,related_name="assigned_files")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="OPEN")
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default="MEDIUM")
    attachment = models.FileField(upload_to="attachments/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.file_no:
            year = timezone.now().year

            last_file = File.objects.filter(
                file_no__startswith=f"FILE-{year}-"
            ).order_by("-id").first()

            if last_file:
                last_number = int(last_file.file_no.split("-")[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.file_no = f"FILE-{year}-{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.file_no

class FileMovement(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("FORWARD", "Forward"),
        ("RETURN", "Return"),
        ("CLOSE", "Close"),
    ]
    file = models.ForeignKey(File,on_delete=models.CASCADE,related_name="movements")
    from_employee = models.ForeignKey(Employee,on_delete=models.PROTECT,related_name="sent_files",null=True,blank=True)
    to_employee = models.ForeignKey(Employee,on_delete=models.PROTECT,related_name="received_files",null=True,blank=True)
    action = models.CharField(max_length=20,choices=ACTION_CHOICES)
    remarks = models.TextField(blank=True)
    moved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["moved_at"]