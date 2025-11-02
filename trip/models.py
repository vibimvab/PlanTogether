from django.conf import settings
from django.db import models


class TravelGroup(models.Model):
    # Django 기본 권한 Group과 이름 충돌을 피하기 위해 TravelGroup으로 명명
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # 생성자(그룹 개설자)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_travel_groups',
    )

    # 멤버십: User <-> Group 다대다를 through로 관리
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMembership',
        related_name='travel_groups',
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    @property
    def member_count(self) -> int:
        return self.members.count()


class GroupMembership(models.Model):
    group = models.ForeignKey(
        TravelGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
    )
    # 필요 시 권한/역할을 구분할 수 있도록 필드 확보
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'user'],
                name='uq_membership_group_user',
            ),
        ]
        indexes = [
            models.Index(fields=['group', 'user']),
        ]
        ordering = ['group_id', 'user_id']


    def __str__(self) -> str:
        return f'{self.user} @ {self.group}'


class Place(models.Model):
    class PlaceType(models.TextChoices):
        RESTAURANT = 'RESTAURANT', '식당'
        CAFE = 'CAFE', '카페'
        ATTRACTION = 'ATTRACTION', '어트랙션'
        SHOPPING = 'SHOPPING', '쇼핑'
        PARK = 'PARK', '공원'
        MUSEUM = 'MUSEUM', '박물관/전시'
        ACCOMMODATION = 'ACCOMMODATION', '숙소'
        OTHER = 'OTHER', '기타'

    # 장소는 특정 그룹에 공유됨
    group = models.ForeignKey(
        TravelGroup,
        on_delete=models.CASCADE,
        related_name='places',
    )

    # 작성자(공유한 사용자)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='places_created',
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    place_type = models.CharField(
        max_length=20,
        choices=PlaceType.choices,
        default=PlaceType.OTHER,
        db_index=True,
    )

    # 위치 관련(옵션)
    address = models.CharField(max_length=255, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['group', 'name']),
            models.Index(fields=['group', 'place_type']),
        ]

    def __str__(self) -> str:
        return f'[{self.group.name}] {self.name}'

    @property
    def recommendations_count(self) -> int:
        return self.recommendations.count()


class Recommendation(models.Model):
    # 추천(좋아요): 한 유저는 같은 장소에 한 번만 추천 가능
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='recommendations',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='place_recommendations',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['place', 'user'],
                name='uq_recommendation_place_user',
            )
        ]
        indexes = [
            models.Index(fields=['place', 'user']),
        ]
        ordering = ['place_id', 'user_id']

    def __str__(self) -> str:
        return f'{self.user} -> {self.place}'
