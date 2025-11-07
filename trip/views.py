# views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import TravelGroup, GroupMembership, Place, Recommendation
from .forms import PlaceForm, GroupForm
from .mixins import GroupMemberRequiredMixin


# 홈 페이지
def index(request):
    return render(request, "trip/index.html")

# 프로필
class UserProfileView(LoginRequiredMixin, ListView):
    model = TravelGroup
    template_name = 'trip/group_place_list.html'
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
    template_name = 'trip/group_form.html'
    success_url = reverse_lazy('trip:group_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        resp = super().form_valid(form)
        # 생성자 자동 가입
        GroupMembership.objects.get_or_create(group=self.object, user=self.request.user, defaults={'is_admin': True})
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
    GroupMembership.objects.get_or_create(group=group, user=request.user)
    return redirect('trip:group_detail', pk=pk)


# 장소
class PlaceCreateView(GroupMemberRequiredMixin, CreateView):
    model = Place
    form_class = PlaceForm
    template_name = 'trip/place_form.html'

    def get_success_url(self):
        return reverse('trip:group_detail', kwargs={'pk': self.kwargs['group_pk']})

    def form_valid(self, form):
        group = TravelGroup.objects.get(pk=self.kwargs['group_pk'])
        form.instance.group = group
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PlaceUpdateView(GroupMemberRequiredMixin, UpdateView):
    model = Place
    form_class = PlaceForm
    template_name = 'trip/place_form.html'

    def get_success_url(self):
        return reverse('trip:group_detail', kwargs={'pk': self.object.group_id})


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
