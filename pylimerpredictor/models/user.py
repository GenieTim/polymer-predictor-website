from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access control
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('researcher', 'Researcher'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text='User role that determines access permissions'
    )
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    
    # Additional fields for user profile
    institution = models.CharField(
        max_length=255,
        blank=True,
        help_text='University, company, or research institution'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Email as the primary login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role
    
    def is_researcher_or_admin(self):
        """Check if user is researcher or admin"""
        return self.role in ['researcher', 'admin']
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
