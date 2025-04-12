import os
import django
import sys
from django.db import connection

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

def print_section(title):
    """Print a section title"""
    print("\n" + "="*70)
    print(f"{title}")
    print("="*70)

def run_query(query):
    """Run a SQL query and print the results in a simple tabular format"""
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        headers = [col[0] for col in cursor.description]
        
        if not results:
            print("No records found.")
            return
            
        # Print headers
        header_row = " | ".join(str(h) for h in headers)
        print(header_row)
        print("-" * len(header_row))
        
        # Print data rows
        for row in results:
            print(" | ".join(str(cell) for cell in row))
            
        print(f"\nTotal records: {len(results)}\n")

# Main script
print("\nQR ATTENDANCE SYSTEM DATABASE REPORT")
print("Generated for demonstration to the lecturer")

# Show Branches
print_section("BRANCHES (Programs/Departments)")
run_query("SELECT id, branch FROM FacultyView_branch ORDER BY branch")

# Show Years
print_section("YEARS OF STUDY")
run_query("SELECT id, year FROM FacultyView_year ORDER BY year")

# Show Sections
print_section("SECTIONS/GROUPS")
run_query("SELECT id, section FROM FacultyView_section ORDER BY section")

# Show Students
print_section("STUDENTS")
run_query("""
SELECT 
    s.s_roll AS roll_number, 
    s.s_fname AS first_name, 
    s.s_lname AS last_name, 
    b.branch AS branch, 
    y.year AS year, 
    sec.section AS section
FROM 
    FacultyView_student s
    JOIN FacultyView_branch b ON s.s_branch_id = b.id
    JOIN FacultyView_year y ON s.s_year_id = y.id
    JOIN FacultyView_section sec ON s.s_section_id = sec.id
ORDER BY 
    s.s_roll
""")

# Show Courses/Subjects
print_section("COURSES")
run_query("""
SELECT 
    s.code AS course_code, 
    s.name AS course_name, 
    b.branch AS branch, 
    y.year AS year, 
    sec.section AS section,
    s.enrollment_key
FROM 
    FacultyView_subject s
    JOIN FacultyView_branch b ON s.branch_id = b.id
    JOIN FacultyView_year y ON s.year_id = y.id
    JOIN FacultyView_section sec ON s.section_id = sec.id
ORDER BY 
    s.code
""")

# Show Enrollments
print_section("COURSE ENROLLMENTS")
run_query("""
SELECT 
    s.s_roll AS roll_number,
    s.s_fname || ' ' || s.s_lname AS student_name,
    sub.code AS course_code,
    sub.name AS course_name,
    ce.enrolled_date
FROM 
    FacultyView_courseenrollment ce
    JOIN FacultyView_student s ON ce.student_id = s.s_roll
    JOIN FacultyView_subject sub ON ce.subject_id = sub.id
ORDER BY 
    ce.enrolled_date DESC
""")

# Show Faculty
print_section("FACULTY MEMBERS")
run_query("""
SELECT 
    u.username,
    u.first_name,
    u.last_name,
    up.department
FROM 
    auth_user u
    JOIN AdminPanel_userprofile up ON u.id = up.user_id
WHERE 
    up.role = 'FACULTY'
ORDER BY 
    u.username
""")

# Show Attendance Records
print_section("ATTENDANCE RECORDS")
run_query("""
SELECT 
    s.s_roll AS roll_number,
    s.s_fname || ' ' || s.s_lname AS student_name,
    sub.code AS course_code,
    sub.name AS course_name,
    ar.date,
    ar.time,
    CASE WHEN ar.is_present THEN 'Present' ELSE 'Absent' END as status
FROM 
    FacultyView_attendancerecord ar
    JOIN FacultyView_student s ON ar.student_id = s.s_roll
    JOIN FacultyView_subject sub ON ar.subject_id = sub.id
ORDER BY 
    ar.date DESC, ar.time DESC
""")

print("\nEND OF DATABASE REPORT") 