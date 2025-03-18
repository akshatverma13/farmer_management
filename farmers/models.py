from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class Block(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        pass

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    block = models.ForeignKey('Block', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_users')
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_profiles')
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_profiles')
    image = models.ImageField(upload_to='user_images/', null=True, blank=True, default='user_images/default.jpg')  # Added user profile image

    class Meta:
        indexes = [models.Index(fields=['block', 'created_by'])]

    def __str__(self):
        return self.user.username
    
def validate_aadhar_id(value):
    if not value.isdigit() or len(value) != 12:
        raise ValidationError('Aadhar ID must be exactly 12 digits (numbers only).')

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    aadhar_id = models.CharField(
        max_length=12,
        unique=True,
        validators=[validate_aadhar_id],
        help_text="Enter a 12-digit numeric Aadhar ID."
    )
    block = models.ForeignKey('Block', on_delete=models.CASCADE, related_name='farmers')
    surveyor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmers')
    farm_area = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='farmers_created')
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='farmers_updated')
    image = models.ImageField(upload_to='farmer_images/', null=True, blank=True, default='farmer_images/default.jpg')
    aadhar_image = models.ImageField(upload_to='aadhar_images/', null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['surveyor', 'block']), models.Index(fields=['created_by'])]

    def clean(self):
        # Model-level validation
        validate_aadhar_id(self.aadhar_id)

    def __str__(self):
        return self.name