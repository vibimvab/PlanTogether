# trip/admin.py
from django.contrib import admin
from .models import (
    TravelGroup,
    GroupMember,
    Place,
    TravelGroupPlace,
    Recommendation,
)


# --- Inlines ---
class GroupMembershipInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    autocomplete_fields = ['user']
    fields = ('user', 'is_admin', 'joined_at')
    readonly_fields = ('joined_at',)


class TravelGroupPlaceInline(admin.TabularInline):
    model = TravelGroupPlace
    extra = 0
    autocomplete_fields = ['place', 'created_by']
    fields = ('place', 'place_type', 'nickname', 'description', 'created_by')
    show_change_link = True


class PlaceGroupLinkInline(admin.TabularInline):
    """Place 상세에서 그룹 연결(through)도 함께 보이게"""
    model = TravelGroupPlace
    extra = 0
    autocomplete_fields = ['travel_group', 'created_by']
    fields = ('travel_group', 'place_type', 'nickname', 'description', 'created_by')
    show_change_link = True


# --- ModelAdmins ---
@admin.register(TravelGroup)
class TravelGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_by', 'member_count', 'created_at']
    search_fields = ['name', 'description']
    autocomplete_fields = ['created_by']
    inlines = [GroupMembershipInline, TravelGroupPlaceInline]


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    # Place에는 group/created_by/created_at/place_type 필드가 없음
    list_display = ['id', 'name', 'address', 'groups_count', 'recommendations_count']
    search_fields = ['name', 'address']
    # through(TravelGroupPlace) 경유 필터: 역참조 related_name 사용
    list_filter = (
        'travel_group_links__travel_group',   # 그룹별
    )
    inlines = [PlaceGroupLinkInline]

    def groups_count(self, obj):
        # TravelGroup.places 의 related_name='travel_groups' 기준
        return obj.travel_groups.count()
    groups_count.short_description = 'Groups'


@admin.register(TravelGroupPlace)
class TravelGroupPlaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'travel_group', 'place', 'place_type', 'nickname', 'created_by']
    search_fields = [
        'travel_group__name',
        'place__name',
        'nickname',
        'description',
    ]
    list_filter = ['place_type', 'travel_group', 'created_by']
    autocomplete_fields = ['travel_group', 'place', 'created_by']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'place', 'user', 'created_at']
    # M2M 경유 그룹 필터: Place.travel_groups (related_name='travel_groups')
    list_filter = ['place', 'user', 'place__travel_group_links__travel_group']
    autocomplete_fields = ['place', 'user']
