# urls.py
from django.urls import path
from . import views

app_name = 'trip'

urlpatterns = [
    # 그룹
    path('', views.GroupListView.as_view(), name='group_list'),
    path('groups/new/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/join/', views.join_group, name='group_join'),

    # 장소 (그룹 내부)
    path('groups/<int:group_pk>/places/new/', views.PlaceCreateView.as_view(), name='place_create'),
    path('places/<int:pk>/edit/', views.PlaceUpdateView.as_view(), name='place_update'),
    path('places/<int:pk>/delete/', views.PlaceDeleteView.as_view(), name='place_delete'),

    # 추천 토글
    path('places/<int:pk>/recommend/', views.toggle_recommendation, name='place_recommend'),

    # Top N
    path('groups/<int:pk>/top/', views.TopPlacesView.as_view(), name='group_top_places'),
]
