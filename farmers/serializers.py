from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile, Block, Farmer
from django.core.validators import EmailValidator, MinValueValidator, RegexValidator
from rest_framework.validators import UniqueValidator

# Validate for Aadhar ID
def validate_aadhar_format(value):
    if not value.isdigit() or len(value) != 12:
        raise serializers.ValidationError("Aadhar ID must be a 12-digit number.")
    return value

password_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9@#$%^&+=!]*$',
    message="Password can only contain letters, numbers, and special characters (@#$%^&+=!)."
)

name_validator = RegexValidator(
    regex=r'^[a-zA-Z\s]+$',
    message="Name can only contain letters and spaces."
)

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="This email is already in use.")
        ]
    )
    password = serializers.CharField(
        write_only=True,
        validators=[password_validator]
    )
    group = serializers.CharField(write_only=True)
    block_id = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all(), source='profile.block')
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="This username is already taken.")
        ]
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'group', 'block_id']

    # validator for 'group'
    def validate_group(self, value):
        valid_groups = ['Supervisors', 'Surveyors']
        if value not in valid_groups:
            raise serializers.ValidationError(f"Group must be one of {valid_groups}.")
        return value
    
    # Serializer-level validator for cross-field validation
    def validate(self, data):
        block = data.get('profile', {}).get('block')
        group = data.get('group')
        if group == 'Supervisors' and block:
            # Check if the block already has a supervisor
            if UserProfile.objects.filter(block=block, user__groups__name='Supervisors').exists():
                raise serializers.ValidationError("This block already has a supervisor assigned.")
        return data
    
    def create(self, validated_data):
        group_name = validated_data.pop('group')
        profile_data = validated_data.pop('profile', {})
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            user.delete()
            raise serializers.ValidationError({'group': f"Group '{group_name}' does not exist."})
        UserProfile.objects.create(
            user=user,
            block=profile_data.get('block'),
            created_by=self.context['request'].user,
            last_updated_by=self.context['request'].user
        )
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['group'] = instance.groups.first().name if instance.groups.exists() else None
        representation['block_id'] = instance.profile.block.id if instance.profile.block else None
        return representation

class FarmerSerializer(serializers.ModelSerializer):
    block_id = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all(), source='block', write_only=True)
    block = serializers.CharField(source='block.name', read_only=True)
    created_at = serializers.DateTimeField(required=False)
    aadhar_id = serializers.CharField(
        validators=[
            UniqueValidator(queryset=Farmer.objects.all(), message="This Aadhar ID already exists."),
            validate_aadhar_format
        ]
    )
    farm_area = serializers.FloatField(
        validators=[
            MinValueValidator(0.1, message="Farm area must be greater than 0.")
        ]
    )
    name = serializers.CharField(
        min_length=3,
        error_messages={
            'min_length': "Name must be at least 3 characters long."
        },
        validators=[
            name_validator
        ]
    )

    class Meta:
        model = Farmer
        fields = ['id', 'name', 'aadhar_id', 'block_id', 'block', 'farm_area', 'created_at', 'image', 'aadhar_image']
        extra_kwargs = {
            'image': {'required': False},
            'aadhar_image': {'required': False}
        }

    # Serializer-level validator for cross-field validation
    def validate(self, data):
        block = data.get('block')
        user = self.context['request'].user
        # Ensure the surveyor can only create farmers in their assigned block
        if user.profile.block != block:
            raise serializers.ValidationError("You can only create farmers in your assigned block.")
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('block_id', None)
        return representation