from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model with role management"""
    
    list_display = (
        'email', 'username', 'first_name', 'last_name', 
        'role', 'institution', 'is_active', 'is_staff', 'created_at'
    )
    list_filter = (
        'role', 'is_active', 'is_staff', 'is_superuser', 'created_at'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'institution')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'institution')
        }),
        (_('Permissions'), {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name', 
                'institution', 'role', 'password1', 'password2'
            ),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)


# Customize admin site header
admin.site.site_header = "Pylimer Predictor Administration"
admin.site.site_title = "Pylimer Admin"
admin.site.index_title = "Welcome to Pylimer Predictor Administration"
