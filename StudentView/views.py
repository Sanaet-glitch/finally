from django.shortcuts import render, redirect, get_object_or_404
from FacultyView.models import Student, Subject, AttendanceRecord, CourseEnrollment
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.core.cache import cache
import ipaddress
from ipware import get_client_ip as ipware_get_client_ip
from django.views.decorators.cache import never_cache
import socket
import requests
from requests.exceptions import RequestException

def get_client_ip(request):
    """Get the client's IP address from the request using ipware library"""
    client_ip, is_routable = ipware_get_client_ip(request)
    
    # If we couldn't get a client IP address, use a placeholder
    if client_ip is None:
        client_ip = '0.0.0.0'
    
    # Normalize localhost representations
    if client_ip in ['::1', '::ffff:127.0.0.1']:
        client_ip = '127.0.0.1'
        
    print(f"Client IP detected: {client_ip} (routable: {is_routable})")
    return client_ip

def add_manually_post(request):
    if request.method == "POST":
        # Print form data for debugging
        print("POST data:", request.POST)
        
        student_roll = request.POST.get("student-name")
        subject_id = request.POST.get("subject")
        source = request.POST.get("source")
        
        print(f"Debug: student_roll={student_roll}, subject_id={subject_id}, source={source}")
        
        if not student_roll or not subject_id:
            # Redirect based on source with an error message
            messages.error(request, "Please select a student and subject")
            if source == "faculty":
                return HttpResponseRedirect(f"/add_manually?subject={subject_id}")
            else:
                return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
        
        today = timezone.now().date()
        today_str = today.isoformat()
        
        # Get client IP address
        client_ip = get_client_ip(request)
        print(f"Debug: client_ip={client_ip}")
        
        # Create a cache key for this subject and date
        cache_key = f"attendance_ip_{subject_id}_{today_str}"
        
        # Get the list of IPs that have marked attendance from the cache
        ip_list = cache.get(cache_key, [])
        print(f"Debug: ip_list={ip_list}")
        
        # Special handling for localhost/127.0.0.1 - don't restrict for demo/development
        is_localhost = client_ip in ['127.0.0.1', 'localhost', '::1']
        
        # Check if this IP has already marked attendance - skip check for faculty or localhost in dev mode
        if client_ip in ip_list and source != "faculty" and not is_localhost:
            # IP has already been used to mark attendance
            print("Debug: IP already marked attendance")
            return render(request, "StudentView/AttendanceError.html", {
                "error_message": "Attendance already marked from this device for today.",
                "subject_id": subject_id
            })
        
        try:
            # If we get here, this IP hasn't marked attendance for this subject today (or is faculty/localhost)
            student = get_object_or_404(Student, s_roll=student_roll)
            subject = get_object_or_404(Subject, id=subject_id)
            
            print(f"Debug: Found student={student.s_fname} {student.s_lname}, subject={subject.name}")
            
            # Check if student is enrolled in this subject (skip if coming from faculty)
            if not CourseEnrollment.objects.filter(student=student, subject=subject).exists() and source != "faculty":
                print("Debug: Student not enrolled")
                return render(request, "StudentView/AttendanceError.html", {
                    "error_message": "You are not enrolled in this course. Please enroll first.",
                    "subject_id": subject_id
                })
            
            now = timezone.now().time()
            
            # Create or update attendance record
            record, created = AttendanceRecord.objects.update_or_create(
                student=student,
                subject=subject,
                date=today,
                defaults={
                    'time': now,
                    'is_present': True
                }
            )
            
            print(f"Debug: Attendance recorded, created={created}")
            
            # Add this IP to the list of IPs that have marked attendance 
            # (if not faculty and not localhost in dev mode)
            if source != "faculty" and not is_localhost:
                ip_list.append(client_ip)
                # Store updated IP list in the cache (with a timeout of 24 hours)
                cache.set(cache_key, ip_list, 60 * 60 * 24)
                print("Debug: IP added to cache")
            
            # Redirect based on source
            if source == "faculty":
                messages.success(request, f"Attendance marked for {student.s_fname} {student.s_lname}")
                return HttpResponseRedirect(f"/?subject={subject_id}")
            else:
                student_name = f"{student.s_fname} {student.s_lname}"
                return HttpResponseRedirect(f"/submitted?name={student_name}&subject_name={subject.name}")
                
        except Exception as e:
            # Log the error and show appropriate message
            print(f"Error marking attendance: {str(e)}")
            messages.error(request, f"Error marking attendance: {str(e)}")
            
            if source == "faculty":
                return HttpResponseRedirect(f"/add_manually?subject={subject_id}")
            else:
                return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
    
    # Redirect appropriately if not a POST request
    subject_id = request.GET.get("subject")
    source = request.GET.get("source")
    
    if source == "faculty":
        if subject_id:
            return HttpResponseRedirect(f"/add_manually?subject={subject_id}")
        else:
            return HttpResponseRedirect("/")
    else:
        if subject_id:
            return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
        else:
            return HttpResponseRedirect("/enroll")


def submitted(request):
    """Page shown after successful attendance submission"""
    student_name = request.GET.get("name", "")
    subject_name = request.GET.get("subject_name", "")
    
    context = {
        "student_name": student_name,
        "subject_name": subject_name,
        "show_details": bool(student_name and subject_name)
    }
    
    return render(request, "StudentView/Submitted.html", context)

def student_enrollment(request):
    """View for students to enroll in courses using enrollment keys"""
    if request.method == "POST":
        roll_number = request.POST.get("roll_number")
        course_code = request.POST.get("course_code")
        enrollment_key = request.POST.get("enrollment_key")
        
        # Validate form data
        if not all([roll_number, course_code, enrollment_key]):
            messages.error(request, "All fields are required")
            return redirect('student_enrollment')
        
        # Find the student and subject
        try:
            student = Student.objects.get(s_roll=roll_number)
        except Student.DoesNotExist:
            messages.error(request, f"Student with roll number {roll_number} not found. Please register first.")
            return redirect('student_enrollment')
        
        try:
            subject = Subject.objects.get(code=course_code)
        except Subject.DoesNotExist:
            messages.error(request, f"Course with code {course_code} not found")
            return redirect('student_enrollment')
        
        # Check enrollment key
        if not subject.enrollment_key or subject.enrollment_key != enrollment_key:
            messages.error(request, "Invalid enrollment key")
            return redirect('student_enrollment')
        
        # Check if already enrolled
        if CourseEnrollment.objects.filter(student=student, subject=subject).exists():
            messages.info(request, f"You are already enrolled in {subject.code} - {subject.name}")
            return redirect('student_enrollment')
        
        # Create enrollment
        CourseEnrollment.objects.create(
            student=student,
            subject=subject
        )
        
        messages.success(request, f"Successfully enrolled in {subject.code} - {subject.name}")
        
        context = {
            'subject': subject,
            'student': student,
            'success': True
        }
        
        return render(request, 'StudentView/enrollment_success.html', context)
    
    return render(request, 'StudentView/enroll.html')


def view_student_enrollments(request):
    """View for students to see the courses they're enrolled in"""
    if request.method == "POST":
        roll_number = request.POST.get("roll_number")
        
        if not roll_number:
            messages.error(request, "Roll number is required")
            return redirect('view_student_enrollments')
        
        try:
            student = Student.objects.get(s_roll=roll_number)
        except Student.DoesNotExist:
            messages.error(request, f"Student with roll number {roll_number} not found")
            return redirect('view_student_enrollments')
        
        enrollments = CourseEnrollment.objects.filter(student=student).select_related('subject')
        
        context = {
            'student': student,
            'enrollments': enrollments,
            'show_results': True
        }
        
        return render(request, 'StudentView/student_enrollments.html', context)
    
    return render(request, 'StudentView/student_enrollments.html', {'show_results': False})

@never_cache
def student_attendance(request):
    """View for students to mark attendance by scanning QR code"""
    subject_id = request.GET.get("subject")
    
    # Check for network connectivity to the faculty server
    # This is important when the QR code directs to an IP that's no longer valid
    host_param = request.GET.get('host')
    if host_param:
        original_host = host_param
        try:
            # Try to resolve the host
            socket.gethostbyname(original_host)
            
            # If we got here, the host resolves, but we should check connectivity
            try:
                test_url = f"http://{original_host}:8000/"
                requests.head(test_url, timeout=2)
            except RequestException:
                # Connection failed despite host resolving
                return render(request, "StudentView/ConnectionError.html", {
                    "error_message": f"Could not connect to attendance server at {original_host}. The server may be offline or inaccessible.",
                    "suggestions": [
                        "Make sure you are on the same network as your instructor",
                        "Check if your instructor's server is running",
                        "Try scanning the QR code again (instructor may need to refresh it)",
                        "Ask your instructor to check server connectivity"
                    ]
                })
        except socket.gaierror:
            # Host cannot be resolved - IP address may have changed
            return render(request, "StudentView/ConnectionError.html", {
                "error_message": f"Unable to reach attendance server at {original_host}. The server address may have changed.",
                "suggestions": [
                    "Make sure you are on the same network as your instructor",
                    "Ask your instructor to refresh the QR code as the network address may have changed",
                    "Try scanning the QR code again after instructor refreshes it"
                ]
            })
    
    if subject_id:
        try:
            selected_subject = Subject.objects.get(id=subject_id)
            
            # Render the initial form to enter roll number
            return render(
                request,
                "StudentView/student_attendance_form.html",
                {
                    "subject": selected_subject
                },
            )
        except Subject.DoesNotExist:
            return render(request, "StudentView/AttendanceError.html", {
                "error_message": "Invalid subject or class code."
            })
    else:
        return render(request, "StudentView/AttendanceError.html", {
            "error_message": "No subject selected. Please scan a valid QR code."
        })

def verify_student(request):
    """Verify student roll number and show confirmation page"""
    if request.method == "POST":
        roll_number = request.POST.get("roll_number")
        subject_id = request.POST.get("subject")
        
        if not roll_number or not subject_id:
            messages.error(request, "Roll number and subject are required")
            return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
        
        try:
            subject = Subject.objects.get(id=subject_id)
            try:
                student = Student.objects.get(s_roll=roll_number)
                
                # Check if student is enrolled in this subject
                if not CourseEnrollment.objects.filter(student=student, subject=subject).exists():
                    messages.error(request, f"You are not enrolled in {subject.code} - {subject.name}. Please enroll first.")
                    return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
                
                # Get today's date for display
                today = timezone.now().date()
                
                # Render confirmation page with student details
                return render(
                    request,
                    "StudentView/confirm_attendance.html",
                    {
                        "subject": subject,
                        "student": student,
                        "today": today
                    }
                )
                
            except Student.DoesNotExist:
                messages.error(request, f"Student with roll number {roll_number} not found")
                return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
                
        except Subject.DoesNotExist:
            return render(request, "StudentView/AttendanceError.html", {
                "error_message": "Invalid subject or class code."
            })
    else:
        # If not POST, redirect to student attendance form
        subject_id = request.GET.get("subject")
        if subject_id:
            return HttpResponseRedirect(f"/student/attendance?subject={subject_id}")
        else:
            return HttpResponseRedirect("/enroll")
