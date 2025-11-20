async function updatePlace() {
    const errorDiv = document.getElementById("error-message");
    errorDiv.textContent = "";

    const nickname = document.getElementById("nickname").value.trim();
    const place_type = document.getElementById("place-type").value;
    const description = document.getElementById("description").value.trim();

    if (!nickname) {
        errorDiv.textContent = "장소 이름을 입력해주세요.";
        nicknameInput.focus();
        return;
    }

    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    const payload = {
        nickname: nickname,
        place_type: place_type,
        description: description,
    }

    try {
        const resp = await fetch(`/api/edit_place_link/${placeLinkId}/`, {
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
            console.log(data.error);
            return;
        }

        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            alert("저장 완료!");
        }
    } catch (e) {
        console.error(e);
        errorDiv.textContent = "네트워크 오류가 발생했습니다.";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.getElementById("submit-btn");
    if (submitBtn) {
        submitBtn.addEventListener("click", updatePlace);
    }
});