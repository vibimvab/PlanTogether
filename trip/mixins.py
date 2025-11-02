from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

class GroupMemberRequiredMixin(LoginRequiredMixin):
    group_lookup_kwarg = 'group_pk'  # 기본
    group_attr = 'group'             # 객체에서 group 찾는 필드 이름

    def get_group(self):
        # 리스트/생성 뷰: URL의 group_pk 사용
        if self.group_lookup_kwarg in self.kwargs:
            from .models import TravelGroup
            return TravelGroup.objects.get(pk=self.kwargs[self.group_lookup_kwarg])
        # 업데이트/삭제 뷰: 객체의 group 참조
        obj = self.get_object()
        return getattr(obj, self.group_attr)

    def dispatch(self, request, *args, **kwargs):
        group = self.get_group()
        if not group.members.filter(id=request.user.id).exists():
            raise Http404("그룹 멤버만 접근할 수 있습니다.")
        return super().dispatch(request, *args, **kwargs)
