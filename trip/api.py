from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from rest_framework.routers import DefaultRouter
import json
import requests

from .models import TravelGroup, Place, TravelGroupPlace
from .utils import is_group_member


@login_required
@require_POST
@transaction.atomic
def group_place_create_api(request, group_pk: int):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "잘못된 JSON 형식입니다."}, status=400)

    group = get_object_or_404(TravelGroup, pk=group_pk)

    place_data = payload.get("place")
    if not place_data:
        return JsonResponse({"success": False, "error": "선택된 장소 정보를 받지 못했습니다."}, status=400)

    place_id = place_data.get("id")
    try:    # DB에 이미 존재하는 장소인지 검색
        place = Place.objects.get(pk=place_id)

    except Place.DoesNotExist:  # 존재하지 않을 경우 새로 생성
        place_name = place_data.get("name")
        place_address = place_data.get("address")
        place_lat = place_data.get("lat")
        place_lng = place_data.get("lng")

        if not place_name or not place_address or place_lat is None or place_lng is None:
            return JsonResponse({"success": False, "error": "장소 정보가 부족합니다."}, status=400)

        place = Place.objects.create(
            id=place_id,
            name=place_name,
            address=place_address,
            lat=place_lat,
            lng=place_lng,
            phone=place_data.get("phone"),
            url=place_data.get("url")
        )

    place_type = payload.get("place_type")  # 장소 타입 dropdown 값
    description = payload.get("description")  # 텍스트

    # TravelGroupPlace 생성
    TravelGroupPlace.objects.create(
        travel_group=group,
        place=place,
        place_type=place_type,
        description=description,
        created_by=request.user,
    )

    return JsonResponse({
        "success": True,
        "redirect_url": f"/groups/{group_pk}/",
    })


def group_places_json(request, group_pk):
    links = (
        TravelGroupPlace.objects
        .select_related('place')
        .filter(travel_group_id=group_pk)
    )

    data = []
    for link in links:
        p = link.place
        data.append({
            "link_id": link.id,
            "place_id": p.id,
            "name": link.nickname or p.name,
            "address": p.address,
            "lat": p.lat,
            "lng": p.lng,
            "place_type": link.place_type,
            "description": link.description,
        })

    return JsonResponse({"places": data})