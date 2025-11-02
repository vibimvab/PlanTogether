# Register your models here.
from django.contrib import admin
from .models import TravelGroup, GroupMembership, Place, Recommendation


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    autocomplete_fields = ['user']


@admin.register(TravelGroup)
class TravelGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_by', 'member_count', 'created_at']
    search_fields = ['name', 'description']
    autocomplete_fields = ['created_by']
    inlines = [GroupMembershipInline]


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'group', 'created_by', 'recommendations_count', 'created_at']
    search_fields = ['name', 'description', 'address']
    list_filter = ['group', 'place_type']
    autocomplete_fields = ['group', 'created_by']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'place', 'user', 'created_at']
    list_filter = ['place__group']
    autocomplete_fields = ['place', 'user']
