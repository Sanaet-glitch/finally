import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

from FacultyView.models import Branch, Year, Section, Student, Subject

def create_initial_data():
    # Create branches
    cs, created = Branch.objects.get_or_create(branch="CS")
    it, created = Branch.objects.get_or_create(branch="IT")
    
    # Create years
    year1, created = Year.objects.get_or_create(year=1)
    year2, created = Year.objects.get_or_create(year=2)
    year3, created = Year.objects.get_or_create(year=3)
    year4, created = Year.objects.get_or_create(year=4)
    
    # Create sections
    secA, created = Section.objects.get_or_create(section="A")
    secB, created = Section.objects.get_or_create(section="B")
    
    # Create subjects
    Subject.objects.get_or_create(
        name="Data Structures and Algorithms",
        code="CS201",
        branch=cs,
        year=year2,
        section=secA
    )
    
    Subject.objects.get_or_create(
        name="Database Management Systems",
        code="CS301",
        branch=cs,
        year=year3,
        section=secA
    )
    
    Subject.objects.get_or_create(
        name="Web Development",
        code="IT302",
        branch=it,
        year=year3,
        section=secB
    )
    
    # Create some students
    students_data = [
        {"roll": "CS001", "fname": "John", "lname": "Doe", "branch": cs, "year": year2, "section": secA},
        {"roll": "CS002", "fname": "Jane", "lname": "Smith", "branch": cs, "year": year2, "section": secA},
        {"roll": "CS003", "fname": "Michael", "lname": "Johnson", "branch": cs, "year": year3, "section": secA},
        {"roll": "CS004", "fname": "Emily", "lname": "Brown", "branch": cs, "year": year3, "section": secA},
        {"roll": "IT001", "fname": "David", "lname": "Wilson", "branch": it, "year": year3, "section": secB},
        {"roll": "IT002", "fname": "Sarah", "lname": "Taylor", "branch": it, "year": year3, "section": secB},
    ]
    
    for student in students_data:
        Student.objects.get_or_create(
            s_roll=student["roll"],
            defaults={
                "s_fname": student["fname"],
                "s_lname": student["lname"],
                "s_branch": student["branch"],
                "s_year": student["year"],
                "s_section": student["section"]
            }
        )
    
    print("Initial data created successfully!")

if __name__ == "__main__":
    create_initial_data() 