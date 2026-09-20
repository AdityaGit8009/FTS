"""
URL configuration for ftsproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mainapp import views
from adminapp.views import *
from empapp.views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index, name='index'),
    path('contact/',views.contact, name='contact'),
    path('adminlogin/',views.adminlogin, name='adminlogin'),
    path('userlogin/',views.userlogin, name='userlogin'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    #adminapp urls'
    path('admindash/',admindash, name='admindash'),
    path('adminlogout/',adminlogout, name='adminlogout'),
    path('adddept/',adddept, name='adddept'),
    path('viewdept/',viewdept, name='viewdept'),
    path('editdept/<int:id>/', editdept, name='editdept'),
    path('deletedept/<int:id>/', deletedept, name='deletedept'),
    path('addemp/',addemp, name='addemp'),
    path('viewemp/',viewemp, name='viewemp'),
    path('editemp/<int:id>/', editemp, name='editemp'),
    path('deleteemp/<int:id>/', deleteemp, name='deleteemp'),
    path('viewallfiles/', viewallfiles, name='viewallfiles'),
    path('editfile/<int:id>/', editfile, name='editfile'),
    path('deletefile/<int:id>/', deletefile, name='deletefile'),
    path('changepass/',changepass, name='changepass'),
    path('empdash/',empdash, name='empdash'),
    path('emplogout/',emplogout, name='emplogout'),
    path('viewprofile/',viewprofile, name='viewprofile'),
    path('updateprofile/',updateprofile, name='updateprofile'),
    path('initiatefile/', initiatefile, name='initiatefile'),
    path('viewfiles/', viewfiles, name='viewfiles'),
    path('emp_editfile/<int:id>/', emp_editfile, name='emp_editfile'),
    path('emp_deletefile/<int:id>/', emp_deletefile, name='emp_deletefile'),
    path('forwardfile/<int:id>/', forwardfile, name='forwardfile'),
    path('returnfile/<int:id>/', returnfile, name='returnfile'),
    path('closefile/<int:id>/', closefile, name='closefile'),
    path('emp_changepass/', emp_changepass, name='emp_changepass'),

]

urlpatterns+=static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
