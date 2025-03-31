from django.contrib import admin
from .models import UserProfile, AdminActionLog

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'department')

class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'action', 'details')
    readonly_fields = ('user', 'action', 'details', 'timestamp')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(AdminActionLog, AdminActionLogAdmin)
