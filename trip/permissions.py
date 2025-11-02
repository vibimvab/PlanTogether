from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import TravelGroup, GroupMembership, Place

class IsGroupMember(BasePermission):
    """
    요청 유저가 해당 그룹의 멤버인지 검사.
    - Place 객체는 place.group
    - Group 객체는 self
    - 신규 생성 시 group id는 request.data['group']에서 확인
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Place):
            group = obj.group
        else:
            group = obj if isinstance(obj, TravelGroup) else getattr(obj, 'group', None)
        if group is None:
            return False
        return group.members.filter(id=request.user.id).exists()

    def has_permission(self, request, view):
        # 생성 시에는 body에 group이 있어야 함
        if view.action == 'create' and hasattr(view, 'expects_group_on_create') and view.expects_group_on_create:
            group_id = request.data.get('group')
            if not group_id:
                return False
        return True

class IsPlaceOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'created_by_id', None) == request.user.id
