"""
URL configuration for Corp_University project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from corpU.views import (
    login_view,
    landing_page,
    sessional_login,
    entityRedirection,
    permanent_login,
    about_view,
    sessional_registrationForm,
    submit_form,
    sessional_dashboard,
    validate_slogin,
    validate_plogin,
    permanent_dashboard,
    add_course,
    sessional_assignment,
    course_timetable,
approve,
mycourses
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sessional_login', sessional_login, name="sessional_login"),
    path('', landing_page, name="home"),
    path('entityRedirection', entityRedirection, name="entityRedirection"),
    path('permanent_login', permanent_login, name="permanent_login"),
    path('about_view', about_view, name="about_view"),
    path('sessional_registration', sessional_registrationForm, name="sessional_registrationForm"),
    path('submit_form', submit_form, name="submit_form"),
    path('sessional_dashboard/<str:param1>', sessional_dashboard, name="sessional_dashboard"),
    path('validate_slogin', validate_slogin, name="validate_slogin"),
    path('validate_plogin', validate_plogin, name="validate_plogin"),
    path('permanent_dashboard/<str:param1>/', permanent_dashboard, name='permanent_dashboard'),
    path('add_course', add_course, name='add_course'),
    path('sessional_assignment',sessional_assignment, name='sessional_assignment'),
    path('course_timetable/<str:param1>/', course_timetable, name='course_timetable'),
    path('approve', approve, name='approve'),
    path('mycourses/<str:param1>/', mycourses, name='mycourses'),

]
