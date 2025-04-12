import os
import sys
import django
from django.db import connection
from tabulate import tabulate
import textwrap

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

# Set the width for wrapping description columns
WRAP_WIDTH = 50

def execute_query(query):
    """Execute a SQL query and return results and column names"""
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall(), [col[0] for col in cursor.description]

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"📋 {title}")
    print("="*80)

def print_data(data, headers, tablefmt="pretty"):
    """Print tabulated data with wrapped text in certain columns"""
    if not data:
        print("\n📊 No records found in this table\n")
        return
        
    # Format data as needed (e.g., wrap long text)
    formatted_data = []
    for row in data:
        formatted_row = list(row)
        # Wrap any potential description columns (adjust indices as needed)
        for i, val in enumerate(formatted_row):
            if isinstance(val, str) and len(val) > WRAP_WIDTH and "description" in headers[i].lower():
                formatted_row[i] = textwrap.fill(val, WRAP_WIDTH)
        formatted_data.append(formatted_row)
    
    print(f"\n📊 Records found: {len(data)}")
    print(tabulate(formatted_data, headers=headers, tablefmt=tablefmt))
    print("\n")

def show_students():
    """Display students with their branch, year, and section details"""
    print_header("STUDENTS")
    
    query = """
    SELECT 
        s.s_roll as "Roll Number", 
        s.s_fname as "First Name", 
        s.s_lname as "Last Name", 
        b.branch as "Branch", 
        y.year as "Year", 
        sec.section as "Section"
    FROM 
        FacultyView_student s
        JOIN FacultyView_branch b ON s.s_branch_id = b.id
        JOIN FacultyView_year y ON s.s_year_id = y.id
        JOIN FacultyView_section sec ON s.s_section_id = sec.id
    ORDER BY 
        s.s_roll
    """
    
    data, headers = execute_query(query)
    print_data(data, headers)

def show_courses():
    """Display courses with their branch, year, and section details"""
    print_header("COURSES")
    
    query = """
    SELECT 
        s.id as "ID",
        s.code as "Course Code", 
        s.name as "Course Name", 
        b.branch as "Branch", 
        y.year as "Year", 
        sec.section as "Section",
        s.enrollment_key as "Enrollment Key"
    FROM 
        FacultyView_subject s
        JOIN FacultyView_branch b ON s.branch_id = b.id
        JOIN FacultyView_year y ON s.year_id = y.id
        JOIN FacultyView_section sec ON s.section_id = sec.id
    ORDER BY 
        s.code
    """
    
    data, headers = execute_query(query)
    print_data(data, headers)

def show_enrollments():
    """Display course enrollments with student and course details"""
    print_header("COURSE ENROLLMENTS")
    
    query = """
    SELECT 
        ce.id as "ID",
        s.s_roll as "Roll Number",
        s.s_fname || ' ' || s.s_lname as "Student Name",
        sub.code as "Course Code",
        sub.name as "Course Name",
        ce.enrolled_date as "Enrollment Date"
    FROM 
        FacultyView_courseenrollment ce
        JOIN FacultyView_student s ON ce.student_id = s.s_roll
        JOIN FacultyView_subject sub ON ce.subject_id = sub.id
    ORDER BY 
        ce.enrolled_date DESC
    """
    
    data, headers = execute_query(query)
    print_data(data, headers)

def show_attendance():
    """Display attendance records with student and course details"""
    print_header("ATTENDANCE RECORDS")
    
    query = """
    SELECT 
        ar.id as "ID",
        s.s_roll as "Roll Number",
        s.s_fname || ' ' || s.s_lname as "Student Name",
        sub.code as "Course Code",
        sub.name as "Course Name",
        ar.date as "Date",
        ar.time as "Time",
        CASE WHEN ar.is_present THEN 'Present' ELSE 'Absent' END as "Status"
    FROM 
        FacultyView_attendancerecord ar
        JOIN FacultyView_student s ON ar.student_id = s.s_roll
        JOIN FacultyView_subject sub ON ar.subject_id = sub.id
    ORDER BY 
        ar.date DESC, ar.time DESC
    """
    
    data, headers = execute_query(query)
    print_data(data, headers)

def show_faculty():
    """Display faculty users with their details"""
    print_header("FACULTY MEMBERS")
    
    query = """
    SELECT 
        u.id as "ID",
        u.username as "Username",
        u.first_name as "First Name",
        u.last_name as "Last Name",
        up.department as "Department",
        up.phone as "Phone"
    FROM 
        auth_user u
        JOIN AdminPanel_userprofile up ON u.id = up.user_id
    WHERE 
        up.role = 'FACULTY'
    ORDER BY 
        u.username
    """
    
    data, headers = execute_query(query)
    print_data(data, headers)

def show_branches_years_sections():
    """Display branches, years, and sections in a compact format"""
    # Branches
    print_header("BASIC CONFIGURATION")
    
    # Branches
    query = "SELECT id as 'ID', branch as 'Name' FROM FacultyView_branch ORDER BY branch"
    data, headers = execute_query(query)
    print("\n🏫 BRANCHES:")
    print_data(data, headers)
    
    # Years
    query = "SELECT id as 'ID', year as 'Year' FROM FacultyView_year ORDER BY year"
    data, headers = execute_query(query)
    print("\n🗓️ YEARS:")
    print_data(data, headers)
    
    # Sections
    query = "SELECT id as 'ID', section as 'Section' FROM FacultyView_section ORDER BY section"
    data, headers = execute_query(query)
    print("\n🔠 SECTIONS:")
    print_data(data, headers)

def main():
    """Main function that displays key database tables"""
    print("\n" + "="*80)
    print("📂 QR ATTENDANCE SYSTEM - KEY DATABASE TABLES 📂".center(80))
    print("="*80)
    
    # Show the core data tables
    show_branches_years_sections()
    show_faculty()
    show_students()
    show_courses()
    show_enrollments()
    show_attendance()
    
    print("\n" + "="*80)
    print("END OF DATABASE REPORT".center(80))
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 