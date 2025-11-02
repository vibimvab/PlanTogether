from django.db.models import Count
from rest_framework import viewsets, routers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import TravelGroup, GroupMembership, Place, Recommendation
from .serializers import (
    TravelGroupSerializer, GroupMembershipSerializer,
    PlaceSerializer, RecommendationSerializer,
)
from .permissions import IsGroupMember, IsPlaceOwnerOrReadOnly


class TravelGroupViewSet(viewsets.ModelViewSet):
    """
    /api/groups/
      - GET: 내가 속한 그룹 목록
      - POST: 그룹 생성(자동 가입 + is_admin=True)
    /api/groups/{id}/
      - GET: 상세
      - POST /join/: 그룹 가입
      - GET  /top_places/: 추천수 상위 장소 10개
    """
    queryset = TravelGroup.objects.all().annotate(member_count=Count('members'))
    serializer_class = TravelGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 내가 멤버인 그룹만 보이게
        return (TravelGroup.objects
                .filter(members=self.request.user)
                .annotate(member_count=Count('members'))
                .order_by('-created_at'))

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        GroupMembership.objects.get_or_create(group=group, user=self.request.user, defaults={'is_admin': True})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        group = self.get_object()
        GroupMembership.objects.get_or_create(group=group, user=request.user)
        return Response({"detail": "joined"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsGroupMember])
    def top_places(self, request, pk=None):
        group = self.get_object()
        places = (group.places
                  .annotate(recommendations_count=Count('recommendations'))
                  .order_by('-recommendations_count', '-created_at')[:10])
        data = PlaceSerializer(places, many=True).data
        return Response(data)


class PlaceViewSet(viewsets.ModelViewSet):
    """
    /api/places/
      - GET: (옵션) ?group=<group_id> 로 필터
      - POST: body에 {"group": <id>, "name": ...} 필수
    /api/places/{id}/recommend/ : POST 토글
    """
    serializer_class = PlaceSerializer
    permission_classes = [IsAuthenticated, IsGroupMember & IsPlaceOwnerOrReadOnly]
    expects_group_on_create = True  # permissions에서 사용

    def get_queryset(self):
        qs = Place.objects.all().select_related('group', 'created_by') \
                 .annotate(recommendations_count=Count('recommendations'))
        group_id = self.request.query_params.get('group')
        if group_id:
            qs = qs.filter(group_id=group_id)
        # 내가 멤버인 그룹의 Place만
        return qs.filter(group__members=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        group_id = self.request.data.get('group')
        group = get_object_or_404(TravelGroup, pk=group_id)
        # 멤버만 생성 가능
        if not group.members.filter(id=self.request.user.id).exists():
            return Response({"detail": "Not a group member"}, status=403)
        serializer.save(group=group, created_by=self.request_user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsGroupMember])
    def recommend(self, request, pk=None):
        place = self.get_object()
        # 멤버 확인은 IsGroupMember가 처리
        rec, created = Recommendation.objects.get_or_create(place=place, user=request.user)
        if not created:
            rec.delete()
            return Response({"detail": "unrecommended", "count": place.recommendations.count()})
        return Response({"detail": "recommended", "count": place.recommendations.count()})


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    필요 시 조회용. 보통은 Place.recommend 액션으로 충분.
    """
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 내가 멤버인 그룹의 추천만
        return Recommendation.objects.filter(place__group__members=self.request.user) \
                                     .select_related('place', 'user') \
                                     .order_by('-created_at')


# 라우터 등록
router = routers.DefaultRouter()
router.register(r'groups', TravelGroupViewSet, basename='group')
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
