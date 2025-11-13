let currentPlace = null;  // { id?, name, address, lat, lng }

function getSelectedMode() {
  const radios = document.querySelectorAll('input[name="mode"]');
  for (const r of radios) {
    if (r.checked) return r.value;
  }
  return "name";
}

async function searchPlace() {
  console.log("searchPlace called");
  const q = document.getElementById("place-query").value.trim();
  const mode = getSelectedMode();
  const resultDiv = document.getElementById("search-result");

  if (!q) {
    resultDiv.textContent = "검색어를 입력하세요.";
    return;
  }

  const url = `/trip/api/places/search/?mode=${encodeURIComponent(mode)}&q=${encodeURIComponent(q)}`;

  const resp = await fetch(url);
  const data = await resp.json();

  if (!resp.ok) {
    resultDiv.textContent = data.error || "검색 중 오류가 발생했습니다.";
    return;
  }

  if (!data.exists) {
    // DB에 없는 장소 → Kakao API로 얻은 lat/lng를 data.place로 내려주면 그대로 사용
    resultDiv.textContent = data.message || "새 장소를 생성할 수 있습니다.";
    // 여기서는 lat/lng가 없다고 가정하니, 실제 서비스에서는 반드시 받아와야 함
    currentPlace = {
      id: null,
      name: q,
      address: q,
      lat: data.lat,   // geocoding 추가시
      lng: data.lng,
    };
  } else {
    const p = data.place;
    currentPlace = {
      id: p.id,
      name: p.name,
      address: p.address,
      lat: p.lat,
      lng: p.lng,
    };
    resultDiv.textContent = `${p.name} (${p.address})`;
  }

  // TODO: Kakao 지도에 currentPlace.lat/lng 마커 업데이트
  // renderMap(currentPlace.lat, currentPlace.lng);
}

async function submitPlace() {
  const errorDiv = document.getElementById("error-message");
  errorDiv.textContent = "";

  if (!currentPlace || currentPlace.lat == null || currentPlace.lng == null) {
    errorDiv.textContent = "먼저 장소를 검색해 주세요.";
    return;
  }

  const placeType = document.getElementById("place-type").value;
  const description = document.getElementById("description").value;

  const payload = {
    place: currentPlace,
    place_type: placeType,
    description: description,
  };

  const resp = await fetch(`/trip/api/groups/${groupId}/places/`, {
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

  // 성공 → 그룹 페이지로 이동
  if (data.redirect_url) {
    window.location.href = data.redirect_url;
  } else {
    alert("저장 완료!");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("search-btn").addEventListener("click", searchPlace);
  document.getElementById("submit-btn").addEventListener("click", submitPlace);
});
