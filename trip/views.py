# views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

import config.settings as settings
from .models import TravelGroup, GroupMember, Place, TravelGroupPlace, Recommendation
from .forms import GroupForm, PlaceNameQueryForm, PlaceAddressQueryForm, PlaceSearchResultForm, TravelGroupPlaceForm
from .mixins import GroupMemberRequiredMixin
from .kakao_maps_api import search_places
from .utils import build_choices


### 홈 페이지 ###
def index(request):
    return render(request, "trip/index.html")


### 프로필 ###
class UserProfileView(LoginRequiredMixin, ListView):
    model = TravelGroup
    template_name = 'trip/profile.html'
    context_object_name = 'groups'

    def get_queryset(self):
        # 내가 속한 그룹 + 내가 만든 그룹 우선
        return (TravelGroup.objects
                .filter(members=self.request.user)
                .order_by('-created_at'))


### 그룹 ###
# 그룹 생성
class GroupCreateView(LoginRequiredMixin, CreateView):
    model = TravelGroup
    form_class = GroupForm
    template_name = 'trip/group_create.html'
    success_url = reverse_lazy('trip:profile')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        resp = super().form_valid(form)
        # 생성자 자동 가입
        GroupMember.objects.get_or_create(group=self.object, user=self.request.user, defaults={'is_admin': True})
        return resp


# 장소 view parent class
class GroupDetailView(LoginRequiredMixin, DetailView):
    model = TravelGroup
    context_object_name = 'group'

    def get_queryset(self):
        return (
            TravelGroup.objects
            .prefetch_related(
                "members",
                "place_links__place",    # TravelGroupPlace + Place까지 한 번에
            )
        )

    def dispatch(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.members.filter(id=request.user.id).exists():
            raise Http404("그룹 멤버만 볼 수 있습니다.")
        return super().dispatch(request, *args, **kwargs)


# 장소 리스트로 보기
class GroupPlaceListView(GroupDetailView):
    template_name = 'trip/group_place_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        # 이 그룹에 속한 장소들
        context["place_links"] = group.place_links.select_related("place")
        return context


# 장소 지도에서 보기
class GroupMapView(GroupDetailView):
    template_name = 'trip/group_map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object

        context["KAKAO_JAVASCRIPT_KEY"] = settings.KAKAO_JAVASCRIPT_KEY

        # JS에서 사용할 JSON API URL도 같이 넘겨주고 싶다면
        context["places_json_url"] = reverse(
            "trip:group_places_json",
            kwargs={"group_pk": group.pk},
        )

        # 필요하다면 places도 템플릿에서 직접 쓸 수 있게
        context["places"] = group.place_links.select_related("place")

        return context


class PlaceUpdateView(LoginRequiredMixin, DetailView):
    model = TravelGroupPlace
    template_name = "trip/place_update.html"
    pk_url_kwarg = "place_pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        place_link = self.object
        context["place_link"] = place_link
        context["group"] = place_link.travel_group
        context["place"] = place_link.place
        return context

# 장소 삭제
@login_required
def delete_place(request, pk):
    place = get_object_or_404(TravelGroupPlace, pk=pk)

    group_pk = place.travel_group.pk

    if request.method == "POST":
        place.delete()
        return redirect("trip:group_place_list", pk=group_pk)

    # POST가 아닌 경우 막기
    return HttpResponseNotAllowed(["POST"])


@login_required
def join_group(request, pk):
    group = get_object_or_404(TravelGroup, pk=pk)
    GroupMember.objects.get_or_create(group=group, user=request.user)
    return redirect('trip:group_detail', pk=pk)


# 장소 생성
@login_required
def create_place(request, group_pk):
    group = get_object_or_404(TravelGroup, pk=group_pk)
    return render(request, "trip/place_create.html", {"group": group})
