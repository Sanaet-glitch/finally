from .models import AdminActionLog

def log_admin_action(user, action, details=None):
    """
    Log an administrative action
    
    Args:
        user: The user performing the action
        action: A short description of the action
        details: Additional details about the action (optional)
    
    Returns:
        The created AdminActionLog instance
    """
    log_entry = AdminActionLog.objects.create(
        user=user,
        action=action,
        details=details
    )
    return log_entry 