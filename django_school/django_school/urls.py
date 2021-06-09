from django.urls import include, path
from django.contrib import admin
from classroom.views import classroom, students, teachers
from django.contrib.auth import views as auth_views

urlpatterns = [
	path('admin/', admin.site.urls),
    path('', include('classroom.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', students.StudentSignUpView.as_view(), name='signup'),ls
    path('accounts/signup/teacher/', teachers.TeacherSignUpView.as_view(), name='teacher_signup'),
]
