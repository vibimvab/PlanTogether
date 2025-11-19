document.addEventListener("DOMContentLoaded", async function () {
  const container = document.getElementById("map");
  if (!container) return;

  const placesUrl = container.dataset.placesUrl;
  if (!placesUrl) {
    console.error("placesUrl(data-places-url)이 설정되지 않았어요.");
    return;
  }

  const map = new kakao.maps.Map(container, {
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 5,
  });

  const resp = await fetch(placesUrl);
  const data = await resp.json();
  const places = data.places || [];

  if (places.length === 0) return;

  const bounds = new kakao.maps.LatLngBounds();

  places.forEach(p => {
    const pos = new kakao.maps.LatLng(p.lat, p.lng);

    const marker = new kakao.maps.Marker({
      position: pos,
      map: map,
    });

    const iw = new kakao.maps.InfoWindow({
      content: `
        <div style="padding:5px;font-size:12px;">
          <b>${p.name}</b><br/>
          ${p.address || ""}
        </div>`,
    });

    kakao.maps.event.addListener(marker, "click", () => {
      iw.open(map, marker);
    });

    bounds.extend(pos);
  });

  map.setBounds(bounds);
});
