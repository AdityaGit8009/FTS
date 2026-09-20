from django.test import TestCase, Client
from django.urls import reverse
from mainapp.models import LoginInfo, Department, Employee, File, FileMovement

class FtsSystemTests(TestCase):
    def setUp(self):
        # Create department
        self.dept = Department.objects.create(dept_name="IT")
        
        # Create logins
        self.log_admin = LoginInfo.objects.create(usertype="admin", username="admin@fts.com", password="adminpassword")
        self.log_emp1 = LoginInfo.objects.create(usertype="employee", username="emp1@fts.com", password="password123")
        self.log_emp2 = LoginInfo.objects.create(usertype="employee", username="emp2@fts.com", password="password456")
        
        # Create employees
        self.emp1 = Employee.objects.create(
            log=self.log_emp1, empid="E1", name="Emp One", contactno="12345", email="emp1@fts.com",
            designation="Developer", department=self.dept, address="Addr 1"
        )
        self.emp2 = Employee.objects.create(
            log=self.log_emp2, empid="E2", name="Emp Two", contactno="67890", email="emp2@fts.com",
            designation="Manager", department=self.dept, address="Addr 2"
        )
        
        # Create client
        self.client = Client()

    def test_deletedept_with_active_employees_fails(self):
        # Login as admin
        session = self.client.session
        session['adminid'] = 'admin@fts.com'
        session.save()
        
        # Attempt to delete department
        response = self.client.get(reverse('deletedept', args=[self.dept.id]))
        
        # Verify department was NOT deleted because employees exist
        self.assertTrue(Department.objects.filter(id=self.dept.id).exists())
        self.assertRedirects(response, reverse('viewdept'))

    def test_file_close_restriction(self):
        # Create a file initiated by emp1, currently held by emp2
        file_obj = File.objects.create(
            title="Important Test File", subject="Test Sub", initiated_by=self.emp1,
            current_holder=self.emp2, status="OPEN", priority="HIGH"
        )
        
        # Log in as emp2 (current holder, but NOT initiator)
        session = self.client.session
        session['eid'] = 'emp2@fts.com'
        session.save()
        
        # Attempt to close the file as emp2
        response = self.client.post(reverse('closefile', args=[file_obj.id]), {'remarks': 'Close it!'})
        
        # Verify redirect and that file is still open (unclosed)
        file_obj.refresh_from_db()
        self.assertEqual(file_obj.status, "OPEN")
        self.assertRedirects(response, reverse('viewfiles'))
        
        # Log in as emp1 (initiator)
        session = self.client.session
        session['eid'] = 'emp1@fts.com'
        session.save()
        
        # Attempt to close the file as emp1
        response = self.client.post(reverse('closefile', args=[file_obj.id]), {'remarks': 'Resolution complete'})
        
        # Verify file is closed successfully
        file_obj.refresh_from_db()
        self.assertEqual(file_obj.status, "CLOSED")
        self.assertRedirects(response, reverse('viewfiles'))

    def test_employee_change_password(self):
        # Log in as emp1
        session = self.client.session
        session['eid'] = 'emp1@fts.com'
        session.save()
        
        # Attempt to change password with correct old password
        response = self.client.post(reverse('emp_changepass'), {
            'old_pass': 'password123',
            'new_pass': 'newsecure123',
            'confirm_pass': 'newsecure123'
        })
        
        # Verify change is saved
        self.log_emp1.refresh_from_db()
        self.assertEqual(self.log_emp1.password, 'newsecure123')
        self.assertRedirects(response, reverse('empdash'))

    def test_forgot_password_otp_flow(self):
        # 1. Step 1 - Request OTP
        response = self.client.post(reverse('forgot_password'), {'email': 'emp1@fts.com'})
        self.assertRedirects(response, reverse('forgot_password'))
        
        # Verify session has OTP and reset_email
        self.assertEqual(self.client.session.get('reset_email'), 'emp1@fts.com')
        otp = self.client.session.get('otp')
        self.assertTrue(otp.isdigit() and len(otp) == 6)
        
        # 2. Step 2 - Verify OTP with incorrect code
        response = self.client.post(reverse('forgot_password'), {'otp': '000000'})
        self.assertRedirects(response, reverse('forgot_password'))
        self.log_emp1.refresh_from_db()
        self.assertEqual(self.log_emp1.password, 'password123') # remains unchanged
        
        # 3. Step 2 - Verify OTP with correct code
        # Refresh session to read latest session state
        session = self.client.session
        session['reset_email'] = 'emp1@fts.com'
        session['otp'] = otp
        import time
        session['otp_time'] = time.time()
        session.save()
        
        response = self.client.post(reverse('forgot_password'), {'otp': otp})
        self.assertRedirects(response, reverse('userlogin'))
        
        # Verify password is reset to default '12345678'
        self.log_emp1.refresh_from_db()
        self.assertEqual(self.log_emp1.password, '12345678')

    def test_admin_reset_password(self):
        # Login as admin
        session = self.client.session
        session['adminid'] = 'admin@fts.com'
        session.save()
        
        # Edit employee, providing a new password
        response = self.client.post(reverse('editemp', args=[self.emp1.id]), {
            'empid': 'E1-Updated',
            'name': 'Emp One Updated',
            'contactno': '12345',
            'email': 'emp1@fts.com',
            'designation': 'Developer',
            'dept_id': self.dept.id,
            'password': 'admin_reset_pass_123'
        })
        self.assertRedirects(response, reverse('viewemp'))
        
        # Verify employee password and credentials are updated
        self.log_emp1.refresh_from_db()
        self.assertEqual(self.log_emp1.password, 'admin_reset_pass_123')
        self.emp1.refresh_from_db()
        self.assertEqual(self.emp1.empid, 'E1-Updated')

