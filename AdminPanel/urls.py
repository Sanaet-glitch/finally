from django.urls import path, register_converter
from . import views

# Define a custom path converter to handle slashes in roll numbers
class RollNumberConverter:
    regex = '[-\w\d/.]+'  # match typical roll numbers which may contain slashes
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value

# Register the converter
register_converter(RollNumberConverter, 'roll')

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('faculty/', views.admin_faculty_list, name='admin_faculty_list'),
    path('faculty/create/', views.admin_faculty_create, name='admin_faculty_create'),
    path('faculty/edit/<int:faculty_id>/', views.admin_faculty_edit, name='admin_faculty_edit'),
    path('faculty/delete/<int:faculty_id>/', views.admin_faculty_delete, name='admin_faculty_delete'),
    path('students/', views.admin_student_list, name='admin_student_list'),
    path('students/register/', views.register_student, name='register_student'),
    path('students/edit/<roll:roll_number>/', views.admin_student_edit, name='admin_student_edit'),
    path('students/delete/<roll:roll_number>/', views.admin_student_delete, name='admin_student_delete'),
    path('system-config/', views.admin_system_config, name='admin_system_config'),
    path('action-logs/', views.admin_action_logs, name='admin_action_logs'),
    path('logout/', views.custom_logout, name='admin_logout'),
    
    # Branch management
    path('branches/', views.admin_branch_list, name='admin_branch_list'),
    path('branches/create/', views.admin_branch_create, name='admin_branch_create'),
    path('branches/edit/<int:branch_id>/', views.admin_branch_edit, name='admin_branch_edit'),
    path('branches/delete/<int:branch_id>/', views.admin_branch_delete, name='admin_branch_delete'),
    
    # Year management
    path('years/', views.admin_year_list, name='admin_year_list'),
    path('years/create/', views.admin_year_create, name='admin_year_create'),
    path('years/edit/<int:year_id>/', views.admin_year_edit, name='admin_year_edit'),
    path('years/delete/<int:year_id>/', views.admin_year_delete, name='admin_year_delete'),
    
    # Section management
    path('sections/', views.admin_section_list, name='admin_section_list'),
    path('sections/create/', views.admin_section_create, name='admin_section_create'),
    path('sections/edit/<int:section_id>/', views.admin_section_edit, name='admin_section_edit'),
    path('sections/delete/<int:section_id>/', views.admin_section_delete, name='admin_section_delete'),
] 