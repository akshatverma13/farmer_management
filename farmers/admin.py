from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Block, Farmer

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = 'user'  # Specify the ForeignKey to use (the primary relationship)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

# Unregister and re-register User with the custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Block)
admin.site.register(Farmer)