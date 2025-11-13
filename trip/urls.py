# urls.py
from django.urls import path
from . import views
from . import api

app_name = 'trip'

urlpatterns = [
    # 홈 페이지
    path("", views.index, name="index"),

    # 개인 페이지 (profile)
    path('profile', views.UserProfileView.as_view(), name='profile'),

    # 그룹
    path('groups/new/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupPlaceListView.as_view(), name='group_place_list'),
    path('groups/<int:pk>/map/', views.GroupMapView.as_view(), name='group_map'),
    path('groups/<int:pk>/join/', views.join_group, name='group_join'),

    # 장소 (그룹 내부)
    path('groups/<int:group_pk>/places/new/', views.create_place, name='place_create'),
    # path('places/<int:pk>/edit/', views.PlaceUpdateView.as_view(), name='place_update'),
    path('places/<int:pk>/delete/', views.PlaceDeleteView.as_view(), name='place_delete'),

    # 장소 리스트 API
    path('groups/<int:group_pk>/places/json/', views.group_places_json, name='group_places_json'),

    # 장소 생성 API
    path('api/places/search/', api.place_search_api, name="place_search_api"),
    path('api/groups/<int:group_pk>/places_create/', api.group_place_create_api, name="place_create_api"),

    # 추천 토글
    path('places/<int:pk>/recommend/', views.toggle_recommendation, name='place_recommend'),

    # Top N
    path('groups/<int:pk>/top/', views.TopPlacesView.as_view(), name='group_top_places'),
]
