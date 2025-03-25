from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import UserProfile, Block, Farmer

# UserSerializer remains unchanged
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    group = serializers.CharField(write_only=True)
    block_id = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all(), source='profile.block')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'group', 'block_id']

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
    block_id = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all(), source='block', write_only=True)  # Use for input
    block = serializers.CharField(source='block.name', read_only=True)  # Return block name in response
    created_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Farmer
        fields = ['id', 'name', 'aadhar_id', 'block_id', 'block', 'farm_area', 'created_at', 'image', 'aadhar_image']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('block_id', None)
        return representation