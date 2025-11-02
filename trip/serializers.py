from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import TravelGroup, GroupMembership, Place, Recommendation
from django.db.models import Count

User = get_user_model()

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class GroupMembershipSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = GroupMembership
        fields = ["id", "user", "is_admin", "joined_at"]

class PlaceSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)
    recommendations_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Place
        fields = [
            "id", "group", "created_by",
            "name", "description",
            "place_type",
            "address", "lat", "lng", "url",
            "created_at", "recommendations_count",
        ]
        read_only_fields = ["created_by", "created_at", "recommendations_count"]

class TravelGroupSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TravelGroup
        fields = ["id", "name", "description", "created_by", "member_count", "created_at", "updated_at"]
        read_only_fields = ["created_by", "member_count", "created_at", "updated_at"]

class RecommendationSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = ["id", "place", "user", "created_at"]
        read_only_fields = ["user", "created_at"]
