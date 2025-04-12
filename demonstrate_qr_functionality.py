import os
import django
import sys
import socket
import qrcode
from datetime import datetime
from io import BytesIO

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QR_Attendance_System.settings')
django.setup()

# Import models
from FacultyView.models import Subject, AttendanceRecord, Student

def print_section(title):
    """Print a section title"""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)

def get_ip_address():
    """Detect the local IP address using multiple methods"""
    ip = "127.0.0.1"  # Default fallback
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
    
    try:
        # Get all possible IPs through socket
        hostname = socket.gethostname()
        for ip_address in socket.gethostbyname_ex(hostname)[2]:
            if not ip_address.startswith('127.'):
                all_possible_ips.append(ip_address)
    except Exception as e:
        print(f"Error getting IPs via hostname: {str(e)}")
    
    # Filter for most likely external IPs (192.168.x.x, 10.x.x.x, etc.)
    filtered_ips = [ip for ip in all_possible_ips if 
                   (ip.startswith('192.168.') or 
                    ip.startswith('10.') or 
                    (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31))]
    
    # Use a valid IP from our list, preferring filtered ones
    if filtered_ips:
        ip = filtered_ips[0]  # Use the first valid filtered IP
    elif all_possible_ips:
        ip = all_possible_ips[0]  # Use any IP we found if no filtered ones
    
    return ip, all_possible_ips

def generate_qr_code(link):
    """Generate a QR code for a given link"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    
    # Just return the QR code without additional annotations
    return qr.make_image(fill_color="black", back_color="white")

def simulate_attendance_marking(student, subject):
    """Simulate marking attendance for a student in a subject"""
    now = datetime.now()
    attendance_date = now.date()
    attendance_time = now.time()
    
    # Create or update attendance record (don't actually save to database)
    print(f"✅ Simulating attendance for {student.s_fname} {student.s_lname}")
    print(f"📘 Course: {subject.code} - {subject.name}")
    print(f"📅 Date: {attendance_date}")
    print(f"🕒 Time: {attendance_time}")
    
    # Show the request details that would be processed
    print("\nMock HTTP Request:")
    print(f"- Student Roll: {student.s_roll}")
    print(f"- Subject ID: {subject.id}")
    print(f"- Date: {attendance_date}")
    print(f"- Client IP: {get_ip_address()[0]}")
    
    # Show the database operation that would occur
    print("\nMock Database Operation:")
    print(f"AttendanceRecord.objects.update_or_create(\n"
          f"    student=Student(s_roll='{student.s_roll}'),\n"
          f"    subject=Subject(id={subject.id}),\n"
          f"    date={attendance_date},\n"
          f"    defaults={{\n"
          f"        'time': {attendance_time},\n"
          f"        'is_present': True\n"
          f"    }}\n"
          f")")

def main():
    print_section("QR ATTENDANCE SYSTEM - DEMONSTRATION OF QR CODE FUNCTIONALITY")
    print("This demonstration shows how the QR code attendance system works.")
    
    # Get IP address information
    ip, all_possible_ips = get_ip_address()
    print(f"\n🌐 Local IP address: {ip}")
    print(f"🌐 All detected IPs: {', '.join(all_possible_ips)}")
    
    # Get subjects from database
    subjects = Subject.objects.all()
    if not subjects:
        print("\n❌ No subjects found in the database.")
        return
    
    # Get a subject for demonstration
    subject = subjects.first()
    print(f"\n📚 Using subject for demo: {subject.code} - {subject.name}")
    
    # Generate QR code info
    qr_link = f"http://{ip}:8000/student/attendance?subject={subject.id}&host={ip}"
    print("\n🔄 Generating QR code for attendance...")
    print(f"📱 QR Code contains URL: {qr_link}")
    
    # Generate and save QR code
    qr_img = generate_qr_code(qr_link)
    qr_filename = "demo_qr_code.png"
    qr_img.save(qr_filename)
    print(f"✅ QR code saved to {qr_filename}")
    
    # Get students
    students = Student.objects.filter(s_branch=subject.branch, s_year=subject.year)
    if not students:
        print("\n❌ No students found who can attend this subject.")
        return
    
    # Select a student for demonstration
    student = students.first()
    print(f"\n👨‍🎓 Using student for demo: {student.s_roll} - {student.s_fname} {student.s_lname}")
    
    # Simulate attendance marking
    print_section("ATTENDANCE MARKING SIMULATION")
    simulate_attendance_marking(student, subject)
    
    # Describe the process
    print_section("HOW THE SYSTEM WORKS")
    print("1. Faculty selects a subject in the Faculty View")
    print("2. System automatically detects the local IP address")
    print("3. QR code is generated containing a URL with subject information")
    print("4. Students scan the QR code with their phones")
    print("5. Students are directed to the attendance page for that subject")
    print("6. Students select their roll number to mark attendance")
    print("7. System records attendance with timestamp")
    print("8. System prevents duplicate attendance by tracking IP addresses")
    print("9. Faculty can view real-time attendance and remove proxy entries")
    
    print("\n✅ DEMONSTRATION COMPLETE")

if __name__ == "__main__":
    main() 