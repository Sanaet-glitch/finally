from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import UserProfile, AdminActionLog
from .utils import log_admin_action
from FacultyView.models import Student, Subject, AttendanceRecord, Branch, Year, Section, CourseEnrollment
from django.contrib.auth import logout
import base64
from urllib.parse import unquote

def is_admin(user):
    """Check if a user has admin role"""
    try:
        return user.profile.role == 'ADMIN'
    except:
        return False

def admin_required(view_func):
    """Decorator to require admin role for a view"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            messages.error(request, "You don't have permission to access the admin panel")
            return redirect('faculty_view')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def login_redirect(request):
    """Redirect users based on their role after login"""
    try:
        # Check if user has a profile and what role they have
        profile = UserProfile.objects.get(user=request.user)
        
        if profile.role == 'ADMIN':
            return redirect('admin_dashboard')
        else:
            return redirect('faculty_view')
    except UserProfile.DoesNotExist:
        # If profile doesn't exist, create one with default role and redirect to faculty view
        UserProfile.objects.create(user=request.user, role='FACULTY')
        log_admin_action(request.user, f"System created default faculty profile for user {request.user.username}")
        messages.warning(request, "Your user profile was missing and has been created with default permissions")
        return redirect('faculty_view')

@admin_required
def admin_dashboard(request):
    """Admin dashboard view - simplified for presentation"""
    # Count statistics
    faculty_count = User.objects.filter(profile__role='FACULTY').count()
    student_count = Student.objects.count()
    course_count = Subject.objects.count()
    
    # Get today's attendance count
    today = timezone.now().date()
    attendance_count = AttendanceRecord.objects.filter(date=today).count()
    
    # Log this view for audit purposes
    log_admin_action(request.user, "Viewed admin dashboard")
    
    context = {
        'active_tab': 'dashboard',
        'faculty_count': faculty_count,
        'student_count': student_count,
        'course_count': course_count,
        'attendance_count': attendance_count,
    }
    
    return render(request, 'AdminPanel/dashboard.html', context)

@admin_required
def admin_faculty_list(request):
    """View all faculty members"""
    # Get all faculty users
    faculty_users = User.objects.filter(profile__role='FACULTY')
    
    context = {
        'active_tab': 'faculty',
        'faculty_users': faculty_users
    }
    return render(request, 'AdminPanel/faculty_list.html', context)

@admin_required
def admin_faculty_create(request):
    """Create new faculty member"""
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        department = request.POST.get('department')
        phone = request.POST.get('phone')
        
        # Validate form data
        if not all([first_name, last_name, username, email, password, confirm_password]):
            messages.error(request, "Please fill in all required fields")
            return render(request, 'AdminPanel/faculty_form.html', {'active_tab': 'faculty'})
        
        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'AdminPanel/faculty_form.html', {'active_tab': 'faculty'})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken")
            return render(request, 'AdminPanel/faculty_form.html', {'active_tab': 'faculty'})
        
        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create or get the profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = 'FACULTY'
            if department:
                profile.department = department
            if phone:
                profile.phone = phone
            profile.save()
            
            # Log the action
            log_admin_action(request.user, f"Created faculty user: {username}")
            
            messages.success(request, f"Faculty account for {first_name} {last_name} created successfully")
            return redirect('admin_faculty_list')
            
        except Exception as e:
            messages.error(request, f"Error creating faculty: {str(e)}")
    
    context = {
        'active_tab': 'faculty'
    }
    return render(request, 'AdminPanel/faculty_form.html', context)

@admin_required
def admin_student_list(request):
    """View all students"""
    # Get all students
    students = Student.objects.all().order_by('s_roll')
    
    context = {
        'active_tab': 'students',
        'students': students
    }
    return render(request, 'AdminPanel/student_list.html', context)

@admin_required
def admin_system_config(request):
    """System configuration view"""
    # This is a placeholder - we'll implement this later
    context = {
        'active_tab': 'system'
    }
    return render(request, 'AdminPanel/system_config.html', context)

@admin_required
def admin_action_logs(request):
    """View admin action logs"""
    # This is a placeholder - we'll implement this later
    context = {
        'active_tab': 'logs'
    }
    return render(request, 'AdminPanel/action_logs.html', context)

@admin_required
def register_student(request):
    """Register a new student"""
    # Get all branches, years, and sections for the form
    branches = Branch.objects.all()
    years = Year.objects.all()
    sections = Section.objects.all()
    
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        roll_number = request.POST.get('roll_number')
        branch_id = request.POST.get('branch')
        year_id = request.POST.get('year')
        section_id = request.POST.get('section')
        
        # Validate form data
        if not all([first_name, last_name, roll_number, branch_id, year_id, section_id]):
            messages.error(request, "Please fill in all required fields")
            return render(request, 'AdminPanel/register_student.html', {
                'active_tab': 'students',
                'branches': branches,
                'years': years,
                'sections': sections,
            })
        
        # Check if roll number already exists
        if Student.objects.filter(s_roll=roll_number).exists():
            messages.error(request, f"Student with roll number {roll_number} already exists")
            return render(request, 'AdminPanel/register_student.html', {
                'active_tab': 'students',
                'branches': branches,
                'years': years,
                'sections': sections,
            })
        
        try:
            # Get the branch, year, and section objects
            branch = Branch.objects.get(id=branch_id)
            year = Year.objects.get(id=year_id)
            section = Section.objects.get(id=section_id)
            
            # Create the student
            student = Student.objects.create(
                s_roll=roll_number,
                s_fname=first_name,
                s_lname=last_name,
                s_branch=branch,
                s_year=year,
                s_section=section
            )
            
            # Log the action
            log_admin_action(request.user, f"Registered student: {roll_number} ({first_name} {last_name})")
            
            messages.success(request, f"Student {first_name} {last_name} registered successfully with roll number {roll_number}")
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error registering student: {str(e)}")
    
    context = {
        'active_tab': 'students',
        'branches': branches,
        'years': years,
        'sections': sections,
    }
    
    return render(request, 'AdminPanel/register_student.html', context)

def custom_logout(request):
    """Custom logout view that works with both GET and POST methods"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')

@admin_required
def admin_branch_list(request):
    """View all branches"""
    branches = Branch.objects.all().order_by('branch')
    
    context = {
        'active_tab': 'branches',
        'branches': branches
    }
    
    log_admin_action(request.user, "Viewed branch list")
    return render(request, 'AdminPanel/branch_list.html', context)

@admin_required
def admin_branch_create(request):
    """Create a new branch"""
    if request.method == "POST":
        branch_name = request.POST.get('branch_name')
        
        if not branch_name:
            messages.error(request, "Branch name is required")
            return redirect('admin_branch_create')
        
        # Check if branch already exists
        if Branch.objects.filter(branch=branch_name).exists():
            messages.error(request, f"Branch '{branch_name}' already exists")
            return redirect('admin_branch_create')
        
        # Create the branch
        branch = Branch.objects.create(branch=branch_name)
        
        log_admin_action(request.user, f"Created branch: {branch_name}")
        messages.success(request, f"Branch '{branch_name}' created successfully")
        return redirect('admin_branch_list')
    
    context = {
        'active_tab': 'branches'
    }
    return render(request, 'AdminPanel/branch_form.html', context)

@admin_required
def admin_branch_edit(request, branch_id):
    """Edit an existing branch"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    if request.method == "POST":
        branch_name = request.POST.get('branch_name')
        
        if not branch_name:
            messages.error(request, "Branch name is required")
            return redirect('admin_branch_edit', branch_id=branch_id)
        
        # Check if branch name already exists (excluding current branch)
        if Branch.objects.filter(branch=branch_name).exclude(id=branch_id).exists():
            messages.error(request, f"Branch '{branch_name}' already exists")
            return redirect('admin_branch_edit', branch_id=branch_id)
        
        # Update the branch
        old_name = branch.branch
        branch.branch = branch_name
        branch.save()
        
        log_admin_action(request.user, f"Updated branch from '{old_name}' to '{branch_name}'")
        messages.success(request, f"Branch updated successfully")
        return redirect('admin_branch_list')
    
    context = {
        'active_tab': 'branches',
        'branch': branch
    }
    return render(request, 'AdminPanel/branch_form.html', context)

@admin_required
def admin_branch_delete(request, branch_id):
    """Delete a branch"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    if request.method == "POST":
        force_delete = request.POST.get('force_delete') == 'true'
        
        # Check if branch is in use
        if Student.objects.filter(s_branch=branch).exists():
            messages.error(request, f"Cannot delete branch '{branch.branch}' as it is assigned to students")
            return redirect('admin_branch_list')
        
        subject_count = Subject.objects.filter(branch=branch).count()
        if subject_count > 0 and not force_delete:
            messages.warning(request, f"Branch '{branch.branch}' is assigned to {subject_count} subjects. Do you want to force delete?")
            context = {
                'active_tab': 'branches',
                'branch': branch,
                'subject_count': subject_count,
                'confirm_force_delete': True
            }
            return render(request, 'AdminPanel/branch_confirm_delete.html', context)
        
        branch_name = branch.branch
        branch.delete()
        
        log_admin_action(request.user, f"Deleted branch: {branch_name}")
        messages.success(request, f"Branch '{branch_name}' deleted successfully")
        
    return redirect('admin_branch_list')

@admin_required
def admin_year_list(request):
    """View all years"""
    years = Year.objects.all().order_by('year')
    
    context = {
        'active_tab': 'years',
        'years': years
    }
    
    log_admin_action(request.user, "Viewed year list")
    return render(request, 'AdminPanel/year_list.html', context)

@admin_required
def admin_year_create(request):
    """Create a new year"""
    if request.method == "POST":
        try:
            year_value = int(request.POST.get('year_value'))
            
            if year_value < 1 or year_value > 4:
                messages.error(request, "Year value must be between 1 and 4")
                return redirect('admin_year_create')
            
            # Check if year already exists
            if Year.objects.filter(year=year_value).exists():
                messages.error(request, f"Year '{year_value}' already exists")
                return redirect('admin_year_create')
            
            # Create the year
            year = Year.objects.create(year=year_value)
            
            log_admin_action(request.user, f"Created year: {year_value}")
            messages.success(request, f"Year '{year_value}' created successfully")
            return redirect('admin_year_list')
            
        except ValueError:
            messages.error(request, "Year value must be a number")
            return redirect('admin_year_create')
    
    context = {
        'active_tab': 'years'
    }
    return render(request, 'AdminPanel/year_form.html', context)

@admin_required
def admin_year_edit(request, year_id):
    """Edit an existing year"""
    year = get_object_or_404(Year, id=year_id)
    
    if request.method == "POST":
        try:
            year_value = int(request.POST.get('year_value'))
            
            if year_value < 1 or year_value > 4:
                messages.error(request, "Year value must be between 1 and 4")
                return redirect('admin_year_edit', year_id=year_id)
            
            # Check if year value already exists (excluding current year)
            if Year.objects.filter(year=year_value).exclude(id=year_id).exists():
                messages.error(request, f"Year '{year_value}' already exists")
                return redirect('admin_year_edit', year_id=year_id)
            
            # Update the year
            old_value = year.year
            year.year = year_value
            year.save()
            
            log_admin_action(request.user, f"Updated year from '{old_value}' to '{year_value}'")
            messages.success(request, f"Year updated successfully")
            return redirect('admin_year_list')
            
        except ValueError:
            messages.error(request, "Year value must be a number")
            return redirect('admin_year_edit', year_id=year_id)
    
    context = {
        'active_tab': 'years',
        'year': year
    }
    return render(request, 'AdminPanel/year_form.html', context)

@admin_required
def admin_year_delete(request, year_id):
    """Delete a year"""
    year = get_object_or_404(Year, id=year_id)
    
    if request.method == "POST":
        # Check if year is in use
        if Student.objects.filter(s_year=year).exists():
            messages.error(request, f"Cannot delete year '{year.year}' as it is assigned to students")
            return redirect('admin_year_list')
        
        if Subject.objects.filter(year=year).exists():
            messages.error(request, f"Cannot delete year '{year.year}' as it is assigned to subjects")
            return redirect('admin_year_list')
        
        year_value = year.year
        year.delete()
        
        log_admin_action(request.user, f"Deleted year: {year_value}")
        messages.success(request, f"Year '{year_value}' deleted successfully")
        
    return redirect('admin_year_list')

@admin_required
def admin_section_list(request):
    """View all sections"""
    sections = Section.objects.all().order_by('section')
    
    context = {
        'active_tab': 'sections',
        'sections': sections
    }
    
    log_admin_action(request.user, "Viewed section list")
    return render(request, 'AdminPanel/section_list.html', context)

@admin_required
def admin_section_create(request):
    """Create a new section"""
    if request.method == "POST":
        section_name = request.POST.get('section_name')
        
        if not section_name:
            messages.error(request, "Section name is required")
            return redirect('admin_section_create')
        
        if len(section_name) > 2:
            messages.error(request, "Section name must be at most 2 characters")
            return redirect('admin_section_create')
        
        # Check if section already exists
        if Section.objects.filter(section=section_name).exists():
            messages.error(request, f"Section '{section_name}' already exists")
            return redirect('admin_section_create')
        
        # Create the section
        section = Section.objects.create(section=section_name)
        
        log_admin_action(request.user, f"Created section: {section_name}")
        messages.success(request, f"Section '{section_name}' created successfully")
        return redirect('admin_section_list')
    
    context = {
        'active_tab': 'sections'
    }
    return render(request, 'AdminPanel/section_form.html', context)

@admin_required
def admin_section_edit(request, section_id):
    """Edit an existing section"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == "POST":
        section_name = request.POST.get('section_name')
        
        if not section_name:
            messages.error(request, "Section name is required")
            return redirect('admin_section_edit', section_id=section_id)
        
        if len(section_name) > 2:
            messages.error(request, "Section name must be at most 2 characters")
            return redirect('admin_section_edit', section_id=section_id)
        
        # Check if section name already exists (excluding current section)
        if Section.objects.filter(section=section_name).exclude(id=section_id).exists():
            messages.error(request, f"Section '{section_name}' already exists")
            return redirect('admin_section_edit', section_id=section_id)
        
        # Update the section
        old_name = section.section
        section.section = section_name
        section.save()
        
        log_admin_action(request.user, f"Updated section from '{old_name}' to '{section_name}'")
        messages.success(request, f"Section updated successfully")
        return redirect('admin_section_list')
    
    context = {
        'active_tab': 'sections',
        'section': section
    }
    return render(request, 'AdminPanel/section_form.html', context)

@admin_required
def admin_section_delete(request, section_id):
    """Delete a section"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == "POST":
        # Check if section is in use
        if Student.objects.filter(s_section=section).exists():
            messages.error(request, f"Cannot delete section '{section.section}' as it is assigned to students")
            return redirect('admin_section_list')
        
        if Subject.objects.filter(section=section).exists():
            messages.error(request, f"Cannot delete section '{section.section}' as it is assigned to subjects")
            return redirect('admin_section_list')
        
        section_name = section.section
        section.delete()
        
        log_admin_action(request.user, f"Deleted section: {section_name}")
        messages.success(request, f"Section '{section_name}' deleted successfully")
        
    return redirect('admin_section_list')

@admin_required
def admin_faculty_edit(request, faculty_id):
    """Edit an existing faculty member"""
    faculty_user = get_object_or_404(User, id=faculty_id)
    faculty_profile = get_object_or_404(UserProfile, user=faculty_user)
    
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        department = request.POST.get('department')
        phone = request.POST.get('phone')
        
        # Optional: Change password if provided
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate form data
        if not all([first_name, last_name, email]):
            messages.error(request, "Please fill in all required fields")
            return render(request, 'AdminPanel/faculty_edit.html', {
                'active_tab': 'faculty',
                'faculty': faculty_user,
                'profile': faculty_profile
            })
            
        # Check if changing password and if passwords match
        if new_password:
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match")
                return render(request, 'AdminPanel/faculty_edit.html', {
                    'active_tab': 'faculty',
                    'faculty': faculty_user,
                    'profile': faculty_profile
                })
            faculty_user.set_password(new_password)
        
        # Update user data
        faculty_user.first_name = first_name
        faculty_user.last_name = last_name
        faculty_user.email = email
        faculty_user.save()
        
        # Update profile data
        faculty_profile.department = department
        faculty_profile.phone = phone
        faculty_profile.save()
        
        # Log the action
        log_admin_action(request.user, f"Updated faculty user: {faculty_user.username}")
        
        messages.success(request, f"Faculty account for {first_name} {last_name} updated successfully")
        return redirect('admin_faculty_list')
    
    context = {
        'active_tab': 'faculty',
        'faculty': faculty_user,
        'profile': faculty_profile
    }
    return render(request, 'AdminPanel/faculty_edit.html', context)

@admin_required
def admin_faculty_delete(request, faculty_id):
    """Delete a faculty member"""
    faculty_user = get_object_or_404(User, id=faculty_id)
    
    if request.method == "POST":
        username = faculty_user.username
        faculty_user.delete()
        
        # Log the action
        log_admin_action(request.user, f"Deleted faculty user: {username}")
        
        messages.success(request, f"Faculty account for {username} deleted successfully")
        
    return redirect('admin_faculty_list')

@admin_required
def admin_student_edit(request, roll_number):
    """Edit an existing student"""
    # URL decode the roll number to handle slashes
    roll_number = unquote(roll_number)
    student = get_object_or_404(Student, s_roll=roll_number)
    
    # Get all branches, years, and sections for the form
    branches = Branch.objects.all()
    years = Year.objects.all()
    sections = Section.objects.all()
    
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        new_roll_number = request.POST.get('roll_number')
        branch_id = request.POST.get('branch')
        year_id = request.POST.get('year')
        section_id = request.POST.get('section')
        
        # Validate form data
        if not all([first_name, last_name, new_roll_number, branch_id, year_id, section_id]):
            messages.error(request, "Please fill in all required fields")
            return render(request, 'AdminPanel/student_form.html', {
                'active_tab': 'students',
                'student': student,
                'branches': branches,
                'years': years,
                'sections': sections,
                'edit_mode': True
            })
            
        # Check if roll number already exists and is not the current one
        if new_roll_number != roll_number and Student.objects.filter(s_roll=new_roll_number).exists():
            messages.error(request, f"Student with roll number {new_roll_number} already exists")
            return render(request, 'AdminPanel/student_form.html', {
                'active_tab': 'students',
                'student': student,
                'branches': branches,
                'years': years,
                'sections': sections,
                'edit_mode': True
            })
            
        try:
            # Get related objects
            branch = get_object_or_404(Branch, id=branch_id)
            year = get_object_or_404(Year, id=year_id)
            section = get_object_or_404(Section, id=section_id)
            
            # Handle case where roll number is changed (primary key)
            if new_roll_number != roll_number:
                # Create new student with new roll number
                new_student = Student.objects.create(
                    s_roll=new_roll_number,
                    s_fname=first_name,
                    s_lname=last_name,
                    s_branch=branch,
                    s_year=year,
                    s_section=section
                )
                
                # Move all related records to the new student
                # CourseEnrollments
                CourseEnrollment.objects.filter(student=student).update(student=new_student)
                
                # AttendanceRecords
                AttendanceRecord.objects.filter(student=student).update(student=new_student)
                
                # Delete old student record
                student.delete()
                
                student_name = f"{first_name} {last_name}"
                log_admin_action(request.user, f"Changed student roll number from {roll_number} to {new_roll_number}")
                messages.success(request, f"Student {student_name} (Roll: {new_roll_number}) updated successfully")
            else:
                # Update existing student
                student.s_fname = first_name
                student.s_lname = last_name
                student.s_branch = branch
                student.s_year = year
                student.s_section = section
                student.save()
                
                student_name = f"{first_name} {last_name}"
                log_admin_action(request.user, f"Updated student: {roll_number}")
                messages.success(request, f"Student {student_name} (Roll: {roll_number}) updated successfully")
                
            return redirect('admin_student_list')
            
        except Exception as e:
            messages.error(request, f"Error updating student: {str(e)}")
            return render(request, 'AdminPanel/student_form.html', {
                'active_tab': 'students',
                'student': student,
                'branches': branches,
                'years': years,
                'sections': sections,
                'edit_mode': True
            })
    
    context = {
        'active_tab': 'students',
        'student': student,
        'branches': branches,
        'years': years,
        'sections': sections,
        'edit_mode': True
    }
    return render(request, 'AdminPanel/student_form.html', context)

@admin_required
def admin_student_delete(request, roll_number):
    """Delete a student"""
    # URL decode the roll number to handle slashes
    roll_number = unquote(roll_number)
    student = get_object_or_404(Student, s_roll=roll_number)
    
    if request.method == "POST":
        student_name = f"{student.s_fname} {student.s_lname}"
        
        # Check if there are attendance records
        attendance_count = AttendanceRecord.objects.filter(student=student).count()
        
        # Optionally, we can add a force delete parameter to override this check
        force_delete = request.POST.get('force_delete') == 'yes'
        
        if attendance_count > 0 and not force_delete:
            messages.warning(request, 
                f"Student {student_name} has {attendance_count} attendance records. "
                "Deleting will remove all attendance history. "
                "To confirm deletion, check the 'Force Delete' option.")
            return render(request, 'AdminPanel/student_delete_confirm.html', {
                'active_tab': 'students',
                'student': student,
                'attendance_count': attendance_count
            })
        
        # Delete all related records first
        CourseEnrollment.objects.filter(student=student).delete()
        AttendanceRecord.objects.filter(student=student).delete()
        
        # Delete the student
        student.delete()
        
        # Log the action
        log_admin_action(request.user, f"Deleted student: {roll_number} ({student_name})")
        
        messages.success(request, f"Student {student_name} (Roll: {roll_number}) deleted successfully")
        
    return redirect('admin_student_list')

@admin_required
def admin_student_edit_encoded(request, encoded_roll_number):
    """Edit an existing student using encoded roll number to avoid URL issues with slashes"""
    # Decode the roll number from base64
    try:
        # First, try base64 decoding
        roll_number = base64.b64decode(encoded_roll_number).decode('utf-8')
    except:
        # If that fails, try simple URL decoding (for backward compatibility)
        roll_number = unquote(encoded_roll_number)
    
    # Delegate to the original function
    return admin_student_edit(request, roll_number)

@admin_required
def admin_student_delete_encoded(request, encoded_roll_number):
    """Delete a student using encoded roll number to avoid URL issues with slashes"""
    # Decode the roll number from base64
    try:
        # First, try base64 decoding
        roll_number = base64.b64decode(encoded_roll_number).decode('utf-8')
    except:
        # If that fails, try simple URL decoding (for backward compatibility)
        roll_number = unquote(encoded_roll_number)
    
    # Delegate to the original function
    return admin_student_delete(request, roll_number)
