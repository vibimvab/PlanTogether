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
@require_GET
def place_search_api(request):
    query = request.GET.get("q", "").strip()
    mode = (request.GET.get("mode") or "name").lower()

    # 쿼리가 없을 경우
    if not query:
        return JsonResponse({"results": []})

    exists = True
    if mode == "address":
        # 주소로 검색
        places = Place.objects.filter(address__icontains=query)
    elif mode == "name":
        # 이름으로 검색
        places = Place.objects.filter(name__icontains=query)
    else:
        return JsonResponse({"error": "잘못된 검색 방식입니다. 장소 이름 또는 주소로 검색 옵션 중 하나를 선택해주세요"})

    place = places.first()
    if not place:
        exists = False
        # Kakao maps api 사용하여 위치 정보 return
        pass

    return JsonResponse({
        "exists" : exists,
        "place": {
            "id": place.id,
            "name": place.name,
            "address": place.address,
            "lat": place.lat,
            "lng": place.lng,
        }
    })


@login_required
@require_POST
@transaction.atomic
def group_place_create_api(request, group_pk: int):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    group = get_object_or_404(TravelGroup, pk=group_pk)

    place_data = payload.get("place") or {}
    place_exists = place_data.get("exists")  # place가 이미 존재하는지

    place_id = place_data.get("id")
    place_name = place_data.get("name")
    place_address = place_data.get("address")
    lat = place_data.get("lat")
    lng = place_data.get("lng")

    place_type = payload.get("place_type")  # dropdown 값
    description = payload.get("description")  # 텍스트

    if not place_name or not place_address or lat is None or lng is None:
        return JsonResponse({"success": False, "error": "장소 정보가 부족합니다."}, status=400)

    # 1) 기존 Place 존재하는 경우
    if place_exists:
        place = get_object_or_404(Place, pk=place_id)

    # 2) 없는 경우: 새 Place 생성
    else:
        place, created = Place.objects.create(
            name=place_name,
            address=place_address,
            defaults={"latitude": lat, "longitude": lng},
        )

    # TravelGroupPlace 생성
    tgp = TravelGroupPlace.objects.create(
        group=group,
        place=place,
        place_type=place_type,
        description=description,
    )

    return JsonResponse({
        "success": True,
        "travel_group_place_id": tgp.id,
        "redirect_url": f"/trip/groups/{group_pk}/",
    })
