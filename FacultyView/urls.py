from . import views
from django.urls import path

urlpatterns = [
    path("", views.faculty_view, name="faculty_view"),
    path("add_manually", views.add_manually, name="add_manually"),
    path("export-attendance", views.export_attendance_csv, name="export_attendance_csv"),
    path("reset-ip-restrictions", views.reset_ip_restrictions, name="reset_ip_restrictions"),
    path("get-attendance-data", views.get_attendance_data, name="get_attendance_data"),
    path("register-student", views.register_student, name="register_student"),
    path("manage-courses", views.manage_courses, name="manage_courses"),
    path("course-enrollments/<int:subject_id>", views.view_course_enrollments, name="course_enrollments"),
]
