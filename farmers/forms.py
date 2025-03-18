from django import forms
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator
from .models import Block, Farmer, UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['image']
        labels = {'image': 'Profile Image'}

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, label="Role")
    block = forms.ModelChoiceField(queryset=Block.objects.all(), required=False, label="Block")
    image = forms.ImageField(required=False, label="Profile Image")

    class Meta:
        model = User
        fields = ['username', 'email', 'group', 'block', 'image']
        labels = {'username': 'Username', 'email': 'Email'}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        group = cleaned_data.get('group')
        block = cleaned_data.get('block')

        if self.instance.pk and not self.instance.check_password(password):
            raise forms.ValidationError("Password is invalid.")
        if group and group.name in ['Supervisors', 'Surveyors'] and not block:
            raise forms.ValidationError(f"A block is required for {group.name}.")
        if group and group.name == 'Supervisors' and block:
            existing_supervisor = UserProfile.objects.filter(
                block=block, user__groups__name='Supervisors'
            ).exclude(user=self.instance if self.instance.pk else None)
            if existing_supervisor.exists():
                raise forms.ValidationError(f"A supervisor is already assigned to the block '{block.name}'.")
        return cleaned_data

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if not self.instance.pk:
            user.set_password(password)
        if user.is_superuser:
            block = None
        else:
            block = self.cleaned_data['block']
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.block = block
            profile.created_by = created_by
            if 'image' in self.cleaned_data and self.cleaned_data['image']:
                profile.image = self.cleaned_data['image']
            profile.save()
            user.groups.set([self.cleaned_data['group']])
        return user

class BlockCreateForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['name']
        labels = {'name': 'Block Name'}

class BlockUpdateForm(forms.ModelForm):
    supervisor = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='Supervisors'), required=False, label="Supervisor")
    surveyors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='Surveyors'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Surveyors"
    )

    class Meta:
        model = Block
        fields = ['name', 'supervisor', 'surveyors']
        labels = {'name': 'Block Name'}

    def clean(self):
        cleaned_data = super().clean()
        supervisor = cleaned_data.get('supervisor')
        block = self.instance
        if supervisor and supervisor.profile.block and supervisor.profile.block != block:
            raise forms.ValidationError("This supervisor is already assigned to another block.")
        return cleaned_data

class FarmerForm(forms.ModelForm):
    aadhar_id = forms.CharField(
        max_length=12,
        min_length=12,  # 12 digits
        required=True,  # Mandatory field
        validators=[RegexValidator(r'^\d{12}$', 'Aadhar ID must be a 12-digit number.')],
        error_messages={
            'required': 'Aadhar ID is required.',
            'max_length': 'Aadhar ID must be exactly 12 digits.',
            'min_length': 'Aadhar ID must be exactly 12 digits.',
        },
        label='Aadhar ID'
    )

    class Meta:
        model = Farmer
        fields = ['name', 'aadhar_id', 'block', 'farm_area']
        labels = {
            'name': 'Farmer Name',
            'aadhar_id': 'Aadhar ID',
            'block': 'Block',
            'farm_area': 'Farm Area (acres)',
        }

    def __init__(self, *args, surveyor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if surveyor:
            self.fields['block'].queryset = Block.objects.filter(id=surveyor.profile.block.id)
            self.fields['block'].initial = surveyor.profile.block
            self.fields['block'].widget.attrs['readonly'] = True
            self.surveyor = surveyor

    def clean(self):
        cleaned_data = super().clean()
        block = cleaned_data.get('block')
        surveyor = getattr(self, 'surveyor', None)
        if surveyor and block != surveyor.profile.block:
            raise forms.ValidationError("You can only manage farmers in your assigned block.")
        return cleaned_data

    def clean_aadhar_id(self):
        aadhar_id = self.cleaned_data['aadhar_id']
        if not aadhar_id.isdigit() or len(aadhar_id) != 12:
            raise forms.ValidationError('Aadhar ID must be exactly 12 digits (numbers only).')
        return aadhar_id
    


class FarmerImageForm(forms.ModelForm):  # For profile image
    class Meta:
        model = Farmer
        fields = ['image']
        labels = {'image': 'Farmer Image'}

class FarmerAadharForm(forms.ModelForm):  # For Aadhar image
    class Meta:
        model = Farmer
        fields = ['aadhar_image']
        labels = {'aadhar_image': 'Aadhar Image'}

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data