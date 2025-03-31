from django.db import models
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.utils import timezone


class Section(models.Model):
    section = models.CharField(max_length=2)

    def __str__(self) -> str:
        return self.section


class Year(models.Model):
    year = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )

    def __str__(self) -> str:
        return str(self.year)


class Branch(models.Model):
    branch = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.branch


class Student(models.Model):
    s_roll = models.CharField(max_length=20, primary_key=True)
    s_fname = models.CharField(max_length=200)
    s_lname = models.CharField(max_length=200)
    s_branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    s_year = models.ForeignKey(Year, on_delete=models.CASCADE)
    s_section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.s_roll} - {self.s_fname} {self.s_lname}"


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    enrollment_key = models.CharField(max_length=20, blank=True, null=True, help_text="Key for students to enroll in this course")
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'subject')
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"
    
    def __str__(self):
        return f"{self.student.s_roll} enrolled in {self.subject.code}"


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    is_present = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('student', 'subject', 'date')
    
    def __str__(self) -> str:
        status = "Present" if self.is_present else "Absent"
        return f"{self.student.s_roll} - {self.subject.code} - {self.date} - {status}"
