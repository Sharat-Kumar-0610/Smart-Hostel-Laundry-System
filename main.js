/* ═══════════════════════════════════════════════════════════
   LaundryOS v2 — main.js
   Global utilities: sidebar, clock, flash dismiss
═══════════════════════════════════════════════════════════ */

// ── Live clock ──────────────────────────────────────────
(function () {
  const el = document.getElementById("live-date");
  if (!el) return;
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleDateString("en-IN", {
      weekday: "short", day: "2-digit", month: "short", year: "numeric"
    }) + "  " + now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  }
  tick();
  setInterval(tick, 30000);
})();

// ── Mobile sidebar toggle ───────────────────────────────
(function () {
  const btn     = document.getElementById("hamburger");
  const sidebar = document.getElementById("sidebar");
  if (!btn || !sidebar) return;

  btn.addEventListener("click", () => sidebar.classList.toggle("open"));

  // Close on outside click
  document.addEventListener("click", (e) => {
    if (sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        e.target !== btn) {
      sidebar.classList.remove("open");
    }
  });
})();

// ── Auto-dismiss flash messages after 5 s ───────────────
(function () {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s ease, max-height .4s ease";
      el.style.opacity = "0";
      el.style.maxHeight = "0";
      el.style.overflow = "hidden";
      setTimeout(() => el.remove(), 420);
    }, 5000);
  });
})();

// ── Student AJAX form (students.html) ───────────────────
const addForm = document.getElementById("add-student-form");
if (addForm) {
  addForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearErrors();

    const fd   = new FormData(this);
    const data = Object.fromEntries(fd.entries());

    let valid = true;
    if (!data.name?.trim())                      { showErr("err-name",  "Name is required");              valid = false; }
    if (!data.register_number?.trim())           { showErr("err-reg",   "Register number required");      valid = false; }
    if (!data.hostel_block)                      { showErr("err-block", "Select a hostel block");          valid = false; }
    if (!data.room_number?.trim())               { showErr("err-room",  "Room number required");           valid = false; }
    if (!/^\d{10}$/.test(data.phone_number||"")){ showErr("err-phone", "Enter a valid 10-digit number"); valid = false; }
    if (!valid) return;

    setBtnLoading(true);

    try {
      const res  = await fetch("/api/students/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json();

      if (json.success) {
        showMsg("s", json.message);
        addForm.reset();
        await refreshStudentTable();
      } else {
        showMsg("e", json.message);
      }
    } catch (_) {
      showMsg("e", "Network error. Please try again.");
    } finally {
      setBtnLoading(false);
    }
  });
}

async function refreshStudentTable() {
  try {
    const res  = await fetch("/api/students");
    const json = await res.json();
    if (!json.success) return;

    const tbody = document.getElementById("student-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    json.students.forEach((s) => {
      const tr = document.createElement("tr");
      tr.className = "row-new";
      tr.innerHTML = `
        <td class="mono dim">${s.StudentID}</td>
        <td><strong>${s.Name}</strong></td>
        <td class="mono dim">${s.RegisterNumber}</td>
        <td><span class="block-chip">${s.HostelBlock}</span></td>
        <td>${s.RoomNumber}</td>
        <td>${s.PhoneNumber}</td>`;
      tbody.appendChild(tr);
      setTimeout(() => tr.classList.remove("row-new"), 1500);
    });

    const chip = document.getElementById("student-count");
    if (chip) chip.textContent = json.students.length;
  } catch (_) {}
}

function showErr(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
}
function clearErrors() {
  document.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
}
function setBtnLoading(on) {
  const t = document.getElementById("btn-text");
  const s = document.getElementById("btn-spinner");
  const b = document.getElementById("submit-btn");
  if (t) t.classList.toggle("hidden", on);
  if (s) s.classList.toggle("hidden", !on);
  if (b) b.disabled = on;
}
function showMsg(type, msg) {
  const el = document.getElementById("form-msg");
  if (!el) return;
  el.innerHTML = `<div class="alert-${type}">${msg}</div>`;
  setTimeout(() => (el.innerHTML = ""), 4500);
}

// ── Live table filter (students page) ──────────────────
const searchStudents = document.getElementById("student-search");
if (searchStudents) {
  searchStudents.addEventListener("input", function () {
    const q = this.value.toLowerCase();
    const rows = document.querySelectorAll("#student-tbody tr");
    let n = 0;
    rows.forEach((r) => {
      const show = r.textContent.toLowerCase().includes(q);
      r.style.display = show ? "" : "none";
      if (show) n++;
    });
    const chip = document.getElementById("student-count");
    if (chip) chip.textContent = n;
  });
}

// ── Row highlight animation for newly added rows ────────
document.querySelectorAll(".table tbody tr").forEach((tr) => {
  tr.addEventListener("mouseenter", () => (tr.style.cursor = "default"));
});
