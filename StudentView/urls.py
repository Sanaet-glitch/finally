from . import views
from django.urls import path

urlpatterns = [
    path("add_manually_post", views.add_manually_post, name="add_manually_post"),
    path("submitted", views.submitted, name="submitted"),
    path("enroll", views.student_enrollment, name="student_enrollment"),
    path("my-courses", views.view_student_enrollments, name="view_student_enrollments"),
    path("student/attendance", views.student_attendance, name="student_attendance"),
    path("verify-student", views.verify_student, name="verify_student"),
]
