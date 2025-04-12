from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from .models import Student, Subject, AttendanceRecord, Branch, Section, Year, CourseEnrollment
import qrcode
import socket
import csv
import json
from django.db.models import Q
from ipware import get_client_ip as ipware_get_client_ip
from django.conf import settings
from AdminPanel.views import admin_required


def qrgenerator(subject_id=None):
    # Enhanced IP detection for more reliable QR code generation
    # Try multiple methods to get the correct local IP address
    ip = "127.0.0.1"  # Default fallback
    
    # Method 1: Socket connection (most reliable for getting IP visible to local network)
    all_possible_ips = []
    
    try:
        # Primary method - socket connection to external service
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        all_possible_ips.append(primary_ip)
    except Exception as e:
        print(f"Error getting IP via primary socket method: {str(e)}")
    
    # Method 2: Get all network interfaces
    try:
        import netifaces
        # Get all interfaces except loopback
        for interface in netifaces.interfaces():
            try:
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    for address in addresses[netifaces.AF_INET]:
                        if 'addr' in address and not address['addr'].startswith('127.'):
                            all_possible_ips.append(address['addr'])
            except Exception as e:
                print(f"Error processing interface {interface}: {str(e)}")
    except ImportError:
        print("netifaces not installed, falling back to socket method")
        try:
            # Get all possible IPs through socket
            hostname = socket.gethostname()
            for ip_address in socket.gethostbyname_ex(hostname)[2]:
                if not ip_address.startswith('127.'):
                    all_possible_ips.append(ip_address)
        except Exception as e:
            print(f"Error getting IPs via hostname: {str(e)}")
    
    # Method 3 (Last resort): Use hostname-based IP as fallback
    if not all_possible_ips:
        try:
            hostname = socket.gethostname()
            fallback_ip = socket.gethostbyname(hostname)
            all_possible_ips.append(fallback_ip)
        except Exception as e:
            print(f"Error getting IP via hostname fallback: {str(e)}")
            # Keep the default 127.0.0.1
            all_possible_ips.append(ip)
    
    # Filter for most likely external IPs (192.168.x.x, 10.x.x.x, etc.)
    filtered_ips = [ip for ip in all_possible_ips if 
                   (ip.startswith('192.168.') or 
                    ip.startswith('10.') or 
                    ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31)]
    
    # Use a valid IP from our list, preferring filtered ones
    if filtered_ips:
        ip = filtered_ips[0]  # Use the first valid filtered IP
    elif all_possible_ips:
        ip = all_possible_ips[0]  # Use any IP we found if no filtered ones
    
    print(f"Using IP address: {ip} (from candidates: {all_possible_ips})")
    
    # Generate multiple QR codes for different possible IPs to improve reliability
    # We'll create one with the most likely IP and one with direct IP
    # Include subject parameter if provided
    # Generate URL with proper parameter formatting
    if subject_id:
        primary_link = f"http://{ip}:8000/student/attendance?subject={subject_id}&host={ip}"
    else:
        primary_link = f"http://{ip}:8000/student/attendance?host={ip}"
    
    # Function to generate and display a QR code
    def generate_qr_code(link, filename="qrcode.png"):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"FacultyView/static/FacultyView/{filename}")

    # Generate the primary QR code
    generate_qr_code(primary_link)
    print(f"Generated QR code with link: {primary_link}")  # Debug output


@login_required
def faculty_view(request):
    subjects = Subject.objects.all()
    selected_subject = None
    
    # Get today's date for filtering
    today = timezone.now().date()
    
    # Handle subject selection
    if request.method == "POST":
        if "select_subject" in request.POST:
            subject_id = request.POST.get("subject")
            if subject_id:
                return HttpResponseRedirect(f"/?subject={subject_id}")
        elif "remove_student" in request.POST:
            student_roll = request.POST.get("student_id")
            subject_id = request.GET.get("subject")
            
            if student_roll and subject_id:
                subject = get_object_or_404(Subject, id=subject_id)
                student = get_object_or_404(Student, s_roll=student_roll)
                
                # Find and delete attendance record
                try:
                    attendance = AttendanceRecord.objects.get(
                        student=student,
                        subject=subject,
                        date=today
                    )
                    attendance.delete()
                except AttendanceRecord.DoesNotExist:
                    pass
                
                return HttpResponseRedirect(f"/?subject={subject_id}")
    
    # Check if a subject is selected
    subject_id = request.GET.get("subject")
    present_students = []
    
    if subject_id:
        selected_subject = get_object_or_404(Subject, id=subject_id)
        
        # Get all attendance records for today and the selected subject
        attendance_records = AttendanceRecord.objects.filter(
            subject=selected_subject,
            date=today,
            is_present=True
        )
        
        # Get the list of present students
        present_students = [record.student for record in attendance_records]
        
        # Generate QR code with subject
        qrgenerator(subject_id)
    else:
        # Generate generic QR code with no subject
        qrgenerator()
    
    context = {
        "subjects": subjects,
        "selected_subject": selected_subject,
        "students": present_students,
        "today": today
    }
    
    return render(request, "FacultyView/FacultyViewIndex.html", context)


@login_required
def add_manually(request):
    """Page for manually adding attendance"""
    # Generate QR code for the add manually page
    subject_id = request.GET.get("subject")
    if subject_id:
        qrgenerator(subject_id)
        selected_subject = get_object_or_404(Subject, id=subject_id)
        
        # Get all students who are enrolled in this subject
        enrolled_students = Student.objects.filter(
            enrollments__subject=selected_subject
        ).distinct()
        
        return render(
            request,
            "StudentView/AddManually.html",
            {
                "subject": selected_subject, 
                "students": enrolled_students,
                "source": "faculty"
            },
        )
    else:
        return HttpResponseRedirect("/")


@login_required
def export_attendance_csv(request):
    subject_id = request.GET.get("subject")
    if not subject_id:
        return HttpResponseRedirect("/")
        
    subject = get_object_or_404(Subject, id=subject_id)
    date_str = request.GET.get("date", timezone.now().date().strftime("%Y-%m-%d"))
    
    try:
        # Parse the date string
        year, month, day = map(int, date_str.split("-"))
        target_date = timezone.datetime(year, month, day).date()
    except (ValueError, TypeError):
        # If date format is incorrect, use today
        target_date = timezone.now().date()
    
    # Get all attendance records for the specified date and subject
    attendance_records = AttendanceRecord.objects.filter(
        subject=subject,
        date=target_date,
        is_present=True
    ).select_related('student')
    
    # Create the HttpResponse with CSV header
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="attendance_{subject.code}_{date_str}.csv"'},
    )
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow(["Roll Number", "First Name", "Last Name", "Time", "Status"])
    
    # Write data rows
    for record in attendance_records:
        writer.writerow([
            record.student.s_roll,
            record.student.s_fname,
            record.student.s_lname,
            record.time.strftime("%H:%M:%S"),
            "Present"
        ])
    
    return response


@login_required
def reset_ip_restrictions(request):
    """Reset IP restrictions for a specific subject and date"""
    if request.method == "POST":
        subject_id = request.POST.get("subject")
        if not subject_id:
            messages.error(request, "No subject selected.")
            return HttpResponseRedirect("/")
        
        # Get today's date
        today = timezone.now().date()
        today_str = today.isoformat()
        
        # Create the cache key used for IP tracking
        cache_key = f"attendance_ip_{subject_id}_{today_str}"
        
        # Delete the cache entry
        cache.delete(cache_key)
        messages.success(request, "IP restrictions reset successfully! Students can now mark attendance again.")
        
        return HttpResponseRedirect(f"/?subject={subject_id}")
    
    # If not a POST request, redirect to faculty view
    return HttpResponseRedirect("/")


@login_required
def get_attendance_data(request):
    """API endpoint to get current attendance data for real-time updates"""
    subject_id = request.GET.get("subject")
    if not subject_id:
        return JsonResponse({"error": "No subject selected"}, status=400)
    
    # Get the subject
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get today's date
    today = timezone.now().date()
    
    # Get all attendance records for today and the selected subject
    attendance_records = AttendanceRecord.objects.filter(
        subject=subject,
        date=today,
        is_present=True
    ).select_related('student')
    
    # Format the data for JSON response
    student_data = []
    for record in attendance_records:
        student_data.append({
            "roll": record.student.s_roll,
            "fname": record.student.s_fname,
            "lname": record.student.s_lname,
            "time": record.time.strftime("%H:%M:%S")
        })
    
    # Return the data as JSON
    return JsonResponse({
        "count": len(student_data),
        "students": student_data
    })


@admin_required
def register_student(request):
    """
    Administrative page for registering new students in the system.
    This page is accessible only to users with admin privileges.
    Students registered here will be eligible for courses based on 
    their branch, year, and section information.
    """
    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        branch_id = request.POST.get('branch')
        year_id = request.POST.get('year')
        section_id = request.POST.get('section')
        
        # Validate form data
        if not all([roll_number, first_name, last_name, branch_id, year_id, section_id]):
            messages.error(request, "All fields are required")
            return redirect('register_student')
        
        # Check if the student already exists
        existing_student = Student.objects.filter(s_roll=roll_number).first()
        if existing_student:
            messages.error(request, f"Student with roll number {roll_number} already exists")
            return redirect('register_student')
        
        # Get objects by ID
        try:
            branch = Branch.objects.get(id=branch_id)
            year = Year.objects.get(id=year_id)
            section = Section.objects.get(id=section_id)
        except (Branch.DoesNotExist, Year.DoesNotExist, Section.DoesNotExist):
            messages.error(request, "Invalid branch, year, or section")
            return redirect('register_student')
        
        # Create student
        student = Student.objects.create(
            s_roll=roll_number,
            s_fname=first_name,
            s_lname=last_name,
            s_branch=branch,
            s_year=year,
            s_section=section
        )
        
        # Get eligible subjects for this student
        eligible_subjects = Subject.objects.filter(branch=branch, year=year)
        if section:
            eligible_subjects = eligible_subjects.filter(
                Q(section=section) | Q(section=None)
            )
        
        context = {
            'branches': Branch.objects.all(),
            'years': Year.objects.all(),
            'sections': Section.objects.all(),
            'registration_success': True,
            'student': student,
            'eligible_subjects': eligible_subjects
        }
        
        messages.success(request, f"Student {first_name} {last_name} registered successfully")
        return render(request, 'FacultyView/RegisterStudent.html', context)
    else:
        context = {
            'branches': Branch.objects.all(),
            'years': Year.objects.all(),
            'sections': Section.objects.all(),
            'registration_success': False
        }
        return render(request, 'FacultyView/RegisterStudent.html', context)


@login_required
def manage_courses(request):
    """Page for faculty to manage courses and enrollment keys"""
    subjects = Subject.objects.all()
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "update_key":
            subject_id = request.POST.get("subject_id")
            enrollment_key = request.POST.get("enrollment_key")
            
            if subject_id and enrollment_key:
                subject = get_object_or_404(Subject, id=subject_id)
                subject.enrollment_key = enrollment_key
                subject.save()
                messages.success(request, f"Enrollment key updated for {subject.code} - {subject.name}")
            else:
                messages.error(request, "Missing subject ID or enrollment key")
                
        elif action == "create_course":
            code = request.POST.get("code")
            name = request.POST.get("name")
            branch_id = request.POST.get("branch")
            year_id = request.POST.get("year")
            section_id = request.POST.get("section", None)
            enrollment_key = request.POST.get("enrollment_key", "")
            
            # Validate data
            if not all([code, name, branch_id, year_id]):
                messages.error(request, "Code, name, branch and year are required")
                return redirect('manage_courses')
            
            # Check if course code already exists
            if Subject.objects.filter(code=code).exists():
                messages.error(request, f"Course with code {code} already exists")
                return redirect('manage_courses')
            
            # Get related objects
            branch = get_object_or_404(Branch, id=branch_id)
            year = get_object_or_404(Year, id=year_id)
            section = None
            if section_id:
                section = get_object_or_404(Section, id=section_id)
            
            # Create new course
            subject = Subject.objects.create(
                code=code,
                name=name,
                branch=branch,
                year=year,
                section=section,
                enrollment_key=enrollment_key
            )
            
            messages.success(request, f"Course {code} - {name} created successfully")
    
    branches = Branch.objects.all()
    years = Year.objects.all()
    sections = Section.objects.all()
    
    # For each subject, get the number of enrolled students
    for subject in subjects:
        subject.enrolled_count = CourseEnrollment.objects.filter(subject=subject).count()
    
    context = {
        'subjects': subjects,
        'branches': branches,
        'years': years,
        'sections': sections
    }
    
    return render(request, 'FacultyView/manage_courses.html', context)


@login_required
def view_course_enrollments(request, subject_id):
    """View students enrolled in a specific course"""
    subject = get_object_or_404(Subject, id=subject_id)
    enrollments = CourseEnrollment.objects.filter(subject=subject).select_related('student')
    
    context = {
        'subject': subject,
        'enrollments': enrollments
    }
    
    return render(request, 'FacultyView/course_enrollments.html', context)
