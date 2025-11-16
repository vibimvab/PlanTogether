// ===== 전역 상태 =====
let map, ps, geocoder, infowindow;
let markers = [];
let currentPlace = null;

// ===== 지도 초기화 =====
function initMap() {
  const container = document.getElementById('map');
  if (!container) return;

  const center = new kakao.maps.LatLng(37.5665, 126.9780); // 서울 시청 근처
  map = new kakao.maps.Map(container, { center, level: 3 });

  // 서비스 객체
  ps = new kakao.maps.services.Places({ map });
  geocoder = new kakao.maps.services.Geocoder();
  infowindow = new kakao.maps.InfoWindow({ zIndex: 1 });
}

// ===== 유틸 =====
function clearListAndMarkers() {
  document.getElementById('placesList').innerHTML = "";
  document.getElementById('pagination').innerHTML = "";
  const msg = document.getElementById('search-result');
  msg.textContent = "";
  markers.forEach(m => m.setMap(null));
  markers = [];
  if (infowindow) infowindow.close();
}

function addMarker(position, idx) {
  const imageSrc = 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_number_blue.png';
  const imageSize = new kakao.maps.Size(36, 37);
  const imgOptions = {
    spriteSize: new kakao.maps.Size(36, 691),
    spriteOrigin: new kakao.maps.Point(0, (idx * 46) + 10),
    offset: new kakao.maps.Point(13, 37)
  };
  const markerImage = new kakao.maps.MarkerImage(imageSrc, imageSize, imgOptions);
  const marker = new kakao.maps.Marker({ position, image: markerImage });
  marker.setMap(map);
  markers.push(marker);
  return marker;
}

function openInfo(marker, title) {
  infowindow.setContent(`<div style="padding:5px;">${title}</div>`);
  infowindow.open(map, marker);
}

// ===== 검색 (브라우저에서 Kakao 호출) =====
async function searchPlace() {
  const q = document.getElementById("place-query").value.trim();
  const resultDiv = document.getElementById("search-result");

  clearListAndMarkers();

  if (!q) {
    resultDiv.textContent = "검색어를 입력하세요.";
    return;
  }

  currentPlace = null;

  // 이름 검색: Places.keywordSearch
  ps.keywordSearch(q, (data, status, pagination) => {
    if (status === kakao.maps.services.Status.OK) {
      renderPlaceResults(data, pagination);
    } else if (status === kakao.maps.services.Status.ZERO_RESULT) {
      resultDiv.textContent = "검색 결과가 존재하지 않습니다.";
    } else {
      resultDiv.textContent = "검색 중 오류가 발생했습니다.";
    }
  },
  { size: 5 }
  );
}

// ===== 결과 렌더링 (장소) =====
function renderPlaceResults(places, pagination) {
  const listEl = document.getElementById('placesList');
  listEl.innerHTML = "";
  const pagEl = document.getElementById('pagination');

  const bounds = new kakao.maps.LatLngBounds();

  places.forEach((p, i) => {
    const pos = new kakao.maps.LatLng(p.y, p.x);
    const marker = addMarker(pos, i);
    bounds.extend(pos);

    // 리스트 아이템
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-start';
    li.innerHTML = `
      <div class="ms-2 me-auto">
        <div class="fw-bold">${p.place_name}</div>
        <div>${p.road_address_name || p.address_name || ""}</div>
        ${p.phone ? `<div class="text-muted">${p.phone}</div>` : ""}
      </div>
      <div class="d-flex gap-2">
        <a class="btn btn-sm btn-outline-secondary" href="${p.place_url}" target="_blank" rel="noreferrer">상세</a>
        <button class="btn btn-sm btn-primary pick-btn">선택</button>
      </div>
    `;

    // hover 동기화
    li.addEventListener('mouseover', () => openInfo(marker, p.place_name));
    li.addEventListener('mouseout', () => infowindow.close());
    kakao.maps.event.addListener(marker, 'mouseover', () => openInfo(marker, p.place_name));
    kakao.maps.event.addListener(marker, 'mouseout', () => infowindow.close());
    kakao.maps.event.addListener(marker, 'click', () => openInfo(marker, p.place_name));

    // 선택 버튼 → currentPlace 설정
    li.querySelector('.pick-btn').addEventListener('click', () => {
      console.log("선택됨:", currentPlace);

      currentPlace = {
        name: p.place_name,
        address: p.road_address_name || p.address_name || "",
        lat: Number(p.y),
        lng: Number(p.x),
        phone: p.phone || null,
        url: p.place_url || null,
        category: p.category_group_code || null,
      };
      // 지도 중심/마커 강조
      map.setCenter(pos);
      openInfo(marker, p.place_name);
      document.getElementById('search-result').textContent = `선택됨: ${p.place_name}`;
    });

    listEl.appendChild(li);
  });

  map.setBounds(bounds);

  // 페이지네이션
  if (pagination) {
    renderPagination(pagination, pagEl);
  }
}

function renderPagination(pagination, container) {
  container.innerHTML = "";
  const frag = document.createDocumentFragment();

  for (let i = 1; i <= pagination.last; i++) {
    const a = document.createElement('a');
    a.href = "#";
    a.textContent = i;
    a.className = (i === pagination.current) ? 'btn btn-sm btn-primary me-1' : 'btn btn-sm btn-outline-primary me-1';
    if (i !== pagination.current) {
      a.onclick = (e) => {
        initMap();
        document.getElementById('placesList').innerHTML = "";
        e.preventDefault();
        pagination.gotoPage(i);
      };
    }
    frag.appendChild(a);
  }
  container.appendChild(frag);
}

// ===== 저장(선택된 1건만 Django로 POST) =====
async function submitPlace() {
  const errorDiv = document.getElementById("error-message");
  errorDiv.textContent = "";

  if (!currentPlace || currentPlace.lat == null || currentPlace.lng == null) {
    errorDiv.textContent = "먼저 검색 결과에서 하나를 선택해 주세요.";
    return;
  }

  const placeType = document.getElementById("place-type").value;
  const description = document.getElementById("description").value;

  const payload = {
    place: currentPlace,
    place_type: placeType,
    description: description,
  };

  try {
    const resp = await fetch(`/api/groups/${groupId}/places_create/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();

    if (!resp.ok || !data.success) {
      errorDiv.textContent = data.error || "저장 중 오류가 발생했습니다.";
      return;
    }

    if (data.redirect_url) {
      window.location.href = data.redirect_url;
    } else {
      alert("저장 완료!");
    }
  } catch (e) {
    errorDiv.textContent = "네트워크 오류가 발생했습니다.";
    console.log(e);
  }
}

// ===== 이벤트 바인딩 =====
document.addEventListener("DOMContentLoaded", () => {
  initMap();

  const qInput = document.getElementById("place-query");
  document.getElementById("search-btn").addEventListener("click", searchPlace);
  document.getElementById("submit-btn").addEventListener("click", submitPlace);

  // 엔터로 검색
  qInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById("search-btn").click();
  });
});
