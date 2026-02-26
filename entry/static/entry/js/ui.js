// Simple UI helpers shared across pages

// Toast
window.toast = (msg, type = "info") => {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  el.style.position = "fixed";
  el.style.left = "50%";
  el.style.bottom = "24px";
  el.style.transform = "translateX(-50%)";
  el.style.color = "#fff";
  el.style.padding = "10px 14px";
  el.style.borderRadius = "8px";
  el.style.fontSize = "14px";
  el.style.zIndex = "9999";
  el.style.background =
    type === "error" ? "#FF6B6B" :
    type === "success" ? "#26C485" : "#333";
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
};

// Activate current nav
(function activateNav() {
  try {
    const path = location.pathname;
    document.querySelectorAll(".nav a").forEach(a => {
      const href = a.getAttribute("href");
      if (href && path.startsWith(href)) a.classList.add("active");
    });
  } catch {}
})();

// Chart.js v2 dark defaults (if available)
(function setChartDefaults(){
  if (window.Chart && Chart.defaults && Chart.defaults.global) {
    const text = "#E9EEF5";
    Chart.defaults.global.defaultFontColor = text;
    Chart.defaults.global.defaultFontFamily = "Inter, Pretendard, sans-serif";
    // per-chart options can still override
  }
})();

// Lucide icons if present
if (window.lucide && typeof window.lucide.createIcons === "function") {
  try { window.lucide.createIcons(); } catch {}
}

// Header avatar support (will no-op if element is absent)
(function loadProfileAvatar(){
  try {
    const src = localStorage.getItem("profileImage");
    const img = document.getElementById("nav-avatar");
    if (img && src) { img.src = src; img.style.display = "block"; }
  } catch {}
})();

// Page hooks
document.addEventListener("DOMContentLoaded", function(){
  try {
    const saved = localStorage.getItem("profileImage");

    // ----- Profile page helpers -----
    const preview = document.getElementById("profile-preview");
    if (preview) {
      const icon = document.querySelector(".profile-image-wrapper i");

      // 미리보기 초기 로드
      if (saved) {
        if (icon) icon.style.display = "none";
        preview.src = saved;
        preview.style.display = "block";
      }

      // 버튼 상태 렌더 함수가 있으면 호출
      if (typeof window.renderProfileButtons === "function") {
        window.renderProfileButtons();
      }

      // 저장 핸들러 (중복/깨진 블록 제거, 한글 문구 복구)
      window.handleSaveImage = function(){
        if (!confirm("저장하시겠습니까?")) return;
        try {
          const dataUrl = preview && preview.src;
          if (!dataUrl) { toast("이미지를 선택하세요.", "error"); return; }
          localStorage.setItem("profileImage", dataUrl);

          // 헤더 아바타 동기화
          const navImg = document.getElementById("nav-avatar");
          if (navImg) { navImg.src = dataUrl; navImg.style.display = "block"; }

          toast("프로필 사진이 저장되었습니다.", "success");
        } catch (e) {
          console.error(e);
          toast("저장 중 오류가 발생했습니다.", "error");
        }

        // 아이콘/프리뷰 토글 및 버튼 상태 갱신
        if (icon) { icon.style.display = "none"; }
        if (preview) { preview.style.display = "block"; }
        if (typeof window.renderProfileButtons === "function") {
          window.renderProfileButtons();
        }
      };
    }

    // Sidebar avatar (add.html 등)
    const sidebarImg = document.querySelector(".sidebar-profile .profile-image img");
    if (sidebarImg && saved) { sidebarImg.src = saved; }

    // Event delegation: 저장 버튼이 있으면 handleSaveImage 호출
    document.addEventListener("click", function(ev){
      const btn = ev.target.closest ? ev.target.closest("#save-image-btn") : null;
      if (btn) {
        ev.preventDefault();
        if (typeof window.handleSaveImage === "function") window.handleSaveImage();
      }
    });

    // 파일 선택 시 버튼 주입/갱신
    const uploader = document.getElementById("image-upload");
    const profileButtons = document.getElementById("profile-buttons");
    const profilePreview = document.getElementById("profile-preview");

    if (uploader && profileButtons && profilePreview) {
      uploader.addEventListener("change", function(){
        // 버튼이 없다면 동적으로 주입
        if (!document.getElementById("save-image-btn")) {
          profileButtons.innerHTML = `
            <button id="save-image-btn" class="btn-secondary">저장</button>
            <button id="cancel-image-btn" class="btn-secondary">취소</button>
          `;

          document.getElementById("save-image-btn")
            .addEventListener("click", function(e){
              e.preventDefault();
              if (typeof window.handleSaveImage === "function") window.handleSaveImage();
            });

          const cancelBtn = document.getElementById("cancel-image-btn");
          if (cancelBtn) {
            cancelBtn.addEventListener("click", function(e){
              e.preventDefault();
              // 선택 초기화 및 페이지 복귀
              try {
                profilePreview.style.display = "none";
                const icon = document.querySelector(".profile-image-wrapper i");
                if (icon) icon.style.display = "block";
                uploader.value = "";
              } catch {}
              // 기본 프로필 페이지 경로 (필요시 수정)
              window.location.href = "/accounts/profile/";
            });
          }
        }
      });
    }

    // Avatar sync: 여러 컨테이너에 반영
    if (saved) {
      const selectors = [
        ".sidebar-profile .profile-image img",
        ".avatar img#nav-avatar"
      ];
      selectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(img => {
          try { img.src = saved; img.style.display = "block"; } catch {}
        });
      });
    }
  } catch {}
});
