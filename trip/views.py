# views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import TravelGroup, GroupMember, Place, TravelGroupPlace, Recommendation
from .forms import GroupForm, PlaceNameQueryForm, PlaceAddressQueryForm, PlaceSearchResultForm, TravelGroupPlaceForm
from .mixins import GroupMemberRequiredMixin
from .kakao_maps_api import search_places
from .utils import build_choices


# 홈 페이지
def index(request):
    return render(request, "trip/index.html")


# 프로필
class UserProfileView(LoginRequiredMixin, ListView):
    model = TravelGroup
    template_name = 'trip/profile.html'
    context_object_name = 'groups'

    def get_queryset(self):
        # 내가 속한 그룹 + 내가 만든 그룹 우선
        return (TravelGroup.objects
                .filter(members=self.request.user)
                .order_by('-created_at'))


# 그룹
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


class GroupPlaceListView(LoginRequiredMixin, DetailView):
    model = TravelGroup
    template_name = 'trip/group_place_list.html'
    context_object_name = 'group'

    def get_queryset(self):
        return TravelGroup.objects.prefetch_related('places__recommendations', 'members')

    def dispatch(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.members.filter(id=request.user.id).exists():
            raise Http404("그룹 멤버만 볼 수 있습니다.")
        return super().dispatch(request, *args, **kwargs)


class GroupMapView(LoginRequiredMixin, DetailView):
    model = TravelGroup
    template_name = 'trip/group_map.html'
    context_object_name = 'group'

    def dispatch(self, request, *args, **kwargs):
        group = self.get_object()
        if not group.members.filter(id=request.user.id).exists():
            raise Http404("그룹 멤버만 볼 수 있습니다.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def join_group(request, pk):
    group = get_object_or_404(TravelGroup, pk=pk)
    GroupMember.objects.get_or_create(group=group, user=request.user)
    return redirect('trip:group_detail', pk=pk)


# 장소
@login_required
def group_place_add(request, group_pk):
    group = get_object_or_404(TravelGroup, pk=group_pk)

    if request.method == "POST" and "search_name" in request.POST:
        qform = PlaceNameQueryForm(request.POST)
        if qform.is_valid():
            results = search_places(qform.cleaned_data["place_name"])  # DB+Kakao
            sform = PlaceSearchResultForm()
            sform.fields["choice"].choices = build_choices(results)  # existing/new
            # new일 때 hidden들 채우기
            return render(request, "trip/place_search_result.html", {"sform": sform, "group": group})

    if request.method == "POST" and "search_address" in request.POST:
        qform = PlaceAddressQueryForm(request.POST)
        if qform.is_valid():
            results = search_places(qform.cleaned_data["address"])
            sform = PlaceSearchResultForm()
            sform.fields["choice"].choices = build_choices(results)
            return render(request, "trip/place_search_result.html", {"sform": sform, "group": group})

    if request.method == "POST" and "choose_result" in request.POST:
        sform = PlaceSearchResultForm(request.POST)
        if sform.is_valid():
            choice = sform.cleaned_data["choice"]
            tform = TravelGroupPlaceForm()
            if choice.startswith("existing:"):
                tform.fields["place_id"].initial = int(choice.split(":")[1])
            else:
                # new 생성용 데이터는 다음 POST에서 사용하도록 hidden으로 넘기거나 세션에 저장
                tform.fields["place_id"].initial = ""
                request.session["new_place"] = {
                    "name": sform.cleaned_data["new_name"],
                    "address": sform.cleaned_data["new_address"],
                    "lat": sform.cleaned_data["new_lat"],
                    "lng": sform.cleaned_data["new_lng"],
                }
            return render(request, "trip/group_place_form.html", {"form": tform, "group": group})

    if request.method == "POST" and "save_group_place" in request.POST:
        tform = TravelGroupPlaceForm(request.POST)
        if tform.is_valid():
            place_id = tform.cleaned_data["place_id"]
            if place_id:
                place = get_object_or_404(Place, pk=place_id)
            else:
                data = request.session.pop("new_place", None)
                if not data:
                    tform.add_error(None, "새 장소 데이터가 없습니다. 다시 검색해주세요.")
                    return render(request, "trip/group_place_form.html", {"form": tform, "group": group})
                place, _ = Place.objects.get_or_create(
                    name=data["name"],
                    address=data["address"] or "",
                    defaults={"lat": data["lat"], "lng": data["lng"]},
                )
            TravelGroupPlace.objects.get_or_create(
                travel_group=group,
                place=place,
                defaults={
                    "place_type": tform.cleaned_data["place_type"],
                    "nickname": tform.cleaned_data.get("nickname", ""),
                    "description": tform.cleaned_data.get("description", ""),
                    "created_by": request.user,
                },
            )
            return redirect("trip:group_place_list", pk=group.pk)

    # 최초 진입 화면: 이름/주소 검색 폼 노출
    return render(request, "trip/place_search.html", {
        "name_form": PlaceNameQueryForm(),
        "addr_form": PlaceAddressQueryForm(),
        "group": group,
    })


# class PlaceUpdateView(GroupMemberRequiredMixin, UpdateView):
#     model = Place
#     form_class = PlaceForm
#     template_name = 'trip/place_form.html'
#
#     def get_success_url(self):
#         return reverse('trip:group_detail', kwargs={'pk': self.object.group_id})


class PlaceDeleteView(GroupMemberRequiredMixin, DeleteView):
    model = Place
    template_name = 'trip/place_confirm_delete.html'

    def get_success_url(self):
        return reverse('trip:group_detail', kwargs={'pk': self.object.group_id})


# 추천 토글
@login_required
def toggle_recommendation(request, pk):
    place = get_object_or_404(Place, pk=pk)
    group = place.group
    if not group.members.filter(id=request.user.id).exists():
        raise Http404("그룹 멤버만 추천할 수 있습니다.")

    rec, created = Recommendation.objects.get_or_create(place=place, user=request.user)
    if not created:
        rec.delete()  # 이미 있으면 취소(토글)
    return redirect('trip:group_detail', pk=group.pk)


# Top N 장소 뷰
class TopPlacesView(LoginRequiredMixin, DetailView):
    model = TravelGroup
    template_name = 'trip/group_top_places.html'
    context_object_name = 'group'

    def get_queryset(self):
        return TravelGroup.objects.prefetch_related('places__recommendations')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['top_places'] = (self.object.places
                             .annotate(num_recs=Count('recommendations'))
                             .order_by('-num_recs', '-created_at')[:10])
        return ctx

@login_required
def group_places_json(request, group_pk):
    group = get_object_or_404(TravelGroup, pk=group_pk)

    # 권한 체크: 그룹 멤버만 볼 수 있게
    if not group.members.filter(id=request.user.id).exists():
        raise Http404("그룹 멤버만 볼 수 있습니다.")

    places = group.places.values(
        'id',
        'name',
        'latitude',
        'longitude',
        'category',  # 있다면
    )

    return JsonResponse(list(places), safe=False)
