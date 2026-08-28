#!/usr/bin/env python3
"""
Census Assistant — apply three fixes to a local checkout.

  1. Remove the "Ask AI" tile from the homepage (home search now goes to
     Records Search instead of the AI chat).
  2. Let the Supervisor tab match a supervisory circle number ("5", "05",
     "005", "Circle 005") in addition to name / user ID / mobile.
  3. Give the admin Upload / Delete flows live status: an upload progress
     bar, an "Indexing..." state, and an optimistic row in the file list.

Usage, from the repository root:

    python apply_census_fixes.py            # apply
    python apply_census_fixes.py --check    # report only, write nothing
    python apply_census_fixes.py --revert   # restore from .bak files

Every edited file is backed up to <file>.bak before the first write.
The script is idempotent: re-running it reports "already applied" and
changes nothing. If any anchor text is missing (because the file has
drifted from what was reviewed), NOTHING is written and the script
exits non-zero naming the anchor it could not find.
"""

import argparse
import os
import shutil
import sys

# --------------------------------------------------------------------------
# frontend/index.html
# --------------------------------------------------------------------------

HTML_QUICK_ACTIONS_OLD = """            <div class="md:col-span-12 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <button onclick="navigateTo('chat')" class="bg-surface-container-lowest border border-outline-variant/30 rounded-2xl p-4 flex flex-col items-center justify-center text-center gap-2 hover:bg-surface-container-low transition-all shadow-[0_2px_4px_rgba(0,0,0,0.02)] active:scale-95">
                <div class="w-11 h-11 rounded-full bg-primary-container/10 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined text-2xl">smart_toy</span>
                </div>
                <span class="text-sm font-semibold text-on-surface" data-i18n="ask_ai">Ask AI</span>
              </button>
"""

HTML_QUICK_ACTIONS_NEW = """            <div class="md:col-span-12 grid grid-cols-2 sm:grid-cols-3 gap-3">
"""

HTML_HOME_PLACEHOLDER_OLD = (
    '              placeholder="Ask anything about Census or search HLB..." '
    'data-i18n-placeholder="search_placeholder"/>'
)
HTML_HOME_PLACEHOLDER_NEW = (
    '              placeholder="Search records by name, ID, mobile, or HLB..." '
    'data-i18n-placeholder="search_placeholder"/>'
)

HTML_SUP_PLACEHOLDER_OLD = '              placeholder="Search supervisors by name, ID, or mobile..."'
HTML_SUP_PLACEHOLDER_NEW = '              placeholder="Search by name, ID, mobile, or circle no. (e.g. 005)..."'

HTML_EXCEL_DROPZONE_OLD = """              <div onclick="document.getElementById('excel-file-input').click()"
                class="border-2 border-dashed border-outline-variant hover:border-primary rounded-xl p-6 flex flex-col items-center justify-center bg-surface hover:bg-surface-container-low transition-all cursor-pointer">"""

HTML_EXCEL_DROPZONE_NEW = """              <div id="excel-dropzone" onclick="document.getElementById('excel-file-input').click()"
                class="border-2 border-dashed border-outline-variant hover:border-primary rounded-xl p-6 flex flex-col items-center justify-center bg-surface hover:bg-surface-container-low transition-all cursor-pointer">"""

HTML_PDF_DROPZONE_OLD = """              <div onclick="document.getElementById('pdf-file-input').click()"
                class="border-2 border-dashed border-outline-variant hover:border-primary rounded-xl p-6 flex flex-col items-center justify-center bg-surface hover:bg-surface-container-low transition-all cursor-pointer flex-1">"""

HTML_PDF_DROPZONE_NEW = """              <div id="pdf-dropzone" onclick="document.getElementById('pdf-file-input').click()"
                class="border-2 border-dashed border-outline-variant hover:border-primary rounded-xl p-6 flex flex-col items-center justify-center bg-surface hover:bg-surface-container-low transition-all cursor-pointer flex-1">"""

HTML_STATUS_BOX_OLD = """            <div id="admin-uploaded-files-list" class="space-y-2">"""

HTML_STATUS_BOX_NEW = """            <div id="admin-upload-status" class="hidden"></div>
            <div id="admin-uploaded-files-list" class="space-y-2">"""

# --------------------------------------------------------------------------
# frontend/app.js
# --------------------------------------------------------------------------

JS_PLACEHOLDERS = [
    (
        '    search_placeholder: "Ask anything about Census or search HLB...",',
        '    search_placeholder: "Search records by name, ID, mobile, or HLB...",',
    ),
    (
        '    search_placeholder: "লোকপিয়ল বা HLB সম্পৰ্কে যিকোনো প্ৰশ্ন সুধক...",',
        '    search_placeholder: "নাম, ID, মোবাইল বা HLB নম্বৰেৰে নথি সন্ধান কৰক...",',
    ),
    (
        '    search_placeholder: "जनगणना या HLB ब्लॉक के बारे में पूछें...",',
        '    search_placeholder: "नाम, ID, मोबाइल या HLB नंबर से रिकॉर्ड खोजें...",',
    ),
    (
        '    search_placeholder: "আদমশুমারি বা HLB ব্লক সম্পর্কে প্রশ্ন করুন...",',
        '    search_placeholder: "নাম, ID, মোবাইল বা HLB নম্বর দিয়ে রেকর্ড খুঁজুন...",',
    ),
]

JS_STATE_OLD = """  pendingMobileForOtp: "",
  searchDebounceTimer: null
};"""

JS_STATE_NEW = """  pendingMobileForOtp: "",
  searchDebounceTimer: null,
  pendingFiles: {},      // filename -> status label, for in-flight upload/delete rows
  uploadInFlight: false
};"""

JS_HOME_SEARCH_OLD = """function executeHomeSearch() {
  const query = document.getElementById("home-search-input").value.trim();
  if (query) {
    quickAsk(query);
  }
}"""

JS_HOME_SEARCH_NEW = """function executeHomeSearch() {
  const query = (document.getElementById("home-search-input").value || "").trim();
  const recordsInput = document.getElementById("records-search-input");
  if (recordsInput) recordsInput.value = query;
  state.recordsFilter = "all";
  navigateTo("search");   // navigateTo() resets the page and calls fetchRecords()
}"""

JS_UPLOAD_START = "async function handleExcelUpload(input) {"
JS_UPLOAD_END = 'async function loadAdminUsers(q = "") {'

JS_UPLOAD_NEW = """// ==================== 9b. ADMIN UPLOAD / DELETE STATUS ====================

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function renderUploadStatus(opts) {
  const box = document.getElementById("admin-upload-status");
  if (!box) return;
  if (!opts) {
    box.className = "hidden";
    box.innerHTML = "";
    return;
  }
  const { title, detail = "", percent = null, tone = "busy" } = opts;
  const tones = {
    busy: "border-primary/40 bg-primary/5 text-primary",
    success: "border-[#2e7d32]/40 bg-[#2e7d32]/10 text-[#2e7d32]",
    error: "border-error/40 bg-error-container/40 text-error"
  };
  const icon = tone === "success" ? "check_circle" : (tone === "error" ? "error" : "progress_activity");
  box.className = `rounded-xl border p-3 flex flex-col gap-2 ${tones[tone]}`;
  box.innerHTML = `
    <div class="flex items-center gap-2">
      <span class="material-symbols-outlined text-base ${tone === "busy" ? "animate-spin" : ""}">${icon}</span>
      <span class="text-xs font-bold">${escapeHtml(title)}</span>
      ${percent !== null ? `<span class="ml-auto text-[11px] font-semibold">${Math.round(percent)}%</span>` : ""}
    </div>
    ${detail ? `<p class="text-[11px] opacity-80">${escapeHtml(detail)}</p>` : ""}
    ${percent !== null ? `<div class="h-1.5 w-full rounded-full bg-black/10 overflow-hidden">
        <div class="h-full bg-current transition-all duration-200" style="width:${Math.max(3, percent)}%"></div>
      </div>` : ""}
  `;
}

function setPendingFile(name, label) {
  if (label) state.pendingFiles[name] = label;
  else delete state.pendingFiles[name];
  paintPendingFiles();
}

// Draws a live row for every in-flight upload/delete at the top of the file
// list, and hides the settled row for the same filename so it never doubles up.
function paintPendingFiles() {
  const container = document.getElementById("admin-uploaded-files-list");
  if (!container) return;
  container.querySelectorAll("[data-pending-file]").forEach(el => el.remove());
  container.querySelectorAll("[data-file]").forEach(row => row.classList.remove("hidden"));

  Object.keys(state.pendingFiles).forEach(name => {
    container.querySelectorAll("[data-file]").forEach(row => {
      if (row.getAttribute("data-file") === name) row.classList.add("hidden");
    });
    const row = document.createElement("div");
    row.setAttribute("data-pending-file", name);
    row.className = "flex items-center gap-3 p-3 rounded-lg border border-primary/40 bg-primary/5";
    row.innerHTML = `
      <div class="loader-spinner-primary shrink-0" style="width:18px;height:18px;border-width:2px;"></div>
      <div class="min-w-0">
        <p class="text-xs font-bold text-on-surface truncate">${escapeHtml(name)}</p>
        <p class="text-[11px] text-primary font-semibold">${escapeHtml(state.pendingFiles[name])}</p>
      </div>
    `;
    container.prepend(row);
  });
}

function setDropzonesDisabled(disabled) {
  ["excel-dropzone", "pdf-dropzone"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle("pointer-events-none", disabled);
    el.classList.toggle("opacity-50", disabled);
  });
}

// XHR instead of fetch so we get real upload progress events.
function uploadWithProgress(path, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", getApiBase() + path);
    if (state.authToken) xhr.setRequestHeader("Authorization", `Bearer ${state.authToken}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress((e.loaded / e.total) * 100);
    };
    xhr.onload = () => {
      let data = {};
      try { data = JSON.parse(xhr.responseText || "{}"); } catch (_) {}
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new Error(data.error || `Upload failed (HTTP ${xhr.status}).`));
    };
    xhr.onerror = () => reject(new Error("Network error during upload."));
    const fd = new FormData();
    fd.append("file", file);
    xhr.send(fd);
  });
}

async function handleSourceUpload(input, endpoint, label) {
  const file = input.files[0];
  input.value = "";
  if (!file) return;
  if (state.uploadInFlight) {
    showToast("Another upload is still running. Please wait for it to finish.");
    return;
  }

  state.uploadInFlight = true;
  setDropzonesDisabled(true);
  setPendingFile(file.name, "Uploading 0%");
  renderUploadStatus({ title: `Uploading ${file.name}`, detail: `${label} • ${formatBytes(file.size)}`, percent: 0 });

  try {
    const data = await uploadWithProgress(endpoint, file, (pct) => {
      const done = pct >= 99.5;
      setPendingFile(file.name, done ? "Indexing…" : `Uploading ${Math.round(pct)}%`);
      renderUploadStatus({
        title: done ? `Indexing ${file.name}…` : `Uploading ${file.name}`,
        detail: done
          ? "Parsing rows and rebuilding the search index. Large PDFs can take a minute."
          : `${label} • ${formatBytes(file.size)}`,
        percent: pct
      });
    });

    if (!data.success) throw new Error(data.error || "Upload failed.");
    renderUploadStatus({ title: `${file.name} indexed`, detail: data.message || "", tone: "success" });
    showToast(data.message || "Upload complete.");
  } catch (err) {
    renderUploadStatus({ title: "Upload failed", detail: err.message, tone: "error" });
    showToast(err.message);
  } finally {
    state.uploadInFlight = false;
    setDropzonesDisabled(false);
    setPendingFile(file.name, null);
    await loadUploadedFiles();
    loadAdminStats();
    setTimeout(() => renderUploadStatus(null), 6000);
  }
}

function handleExcelUpload(input) {
  return handleSourceUpload(input, "/api/admin/upload-excel", "Excel dataset");
}

function handlePdfUpload(input) {
  return handleSourceUpload(input, "/api/admin/upload-pdf", "PDF manual");
}

async function loadUploadedFiles() {
  const container = document.getElementById("admin-uploaded-files-list");
  if (!container) return;

  if (!container.querySelector("[data-file]")) {
    container.innerHTML = `<div class="flex justify-center p-4"><div class="loader-spinner-primary"></div></div>`;
    paintPendingFiles();
  }

  try {
    const res = await apiFetch("/api/admin/uploaded-files");
    const data = await res.json();
    container.innerHTML = "";

    if (!data.files || data.files.length === 0) {
      container.innerHTML = `<p class="text-xs text-on-surface-variant p-3 text-center">No source files detected.</p>`;
      paintPendingFiles();
      return;
    }

    data.files.forEach(f => {
      const isPdf = f.filename.endsWith(".pdf");
      const icon = isPdf ? "picture_as_pdf" : "table_view";
      const iconColor = isPdf ? "text-error" : "text-primary";

      const item = document.createElement("div");
      item.setAttribute("data-file", f.filename);
      item.className = "flex items-center justify-between p-3 rounded-lg border border-outline-variant/30 bg-surface hover:bg-surface-container-low transition-colors";
      item.innerHTML = `
        <div class="flex items-center gap-3 min-w-0">
          <span class="material-symbols-outlined ${iconColor} text-2xl shrink-0">${icon}</span>
          <div class="truncate">
            <p class="text-xs font-bold text-on-surface truncate">${escapeHtml(f.filename)}</p>
            <p class="text-[11px] text-on-surface-variant">${escapeHtml(f.file_type)} • ${escapeHtml(f.size_str)} • Modified ${escapeHtml(f.last_modified)}</p>
          </div>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <button onclick="handleDeleteUploadedFile('${escapeAttr(f.filename)}')" title="Delete File"
            class="w-8 h-8 rounded-full flex items-center justify-center text-error hover:bg-error-container/40 transition-colors">
            <span class="material-symbols-outlined text-base">delete</span>
          </button>
        </div>
      `;
      container.appendChild(item);
    });

    paintPendingFiles();
  } catch (err) {
    container.innerHTML = `<p class="text-xs text-error p-3">Failed to load repository files.</p>`;
  }
}

async function handleDeleteUploadedFile(filename) {
  if (!confirm(`Delete '${filename}'? The knowledge base will be re-indexed.`)) return;

  setPendingFile(filename, "Deleting & re-indexing…");
  renderUploadStatus({ title: `Deleting ${filename}`, detail: "Removing the file and rebuilding the knowledge base…" });

  try {
    const res = await apiFetch(`/api/admin/uploaded-files/${encodeURIComponent(filename)}`, { method: "DELETE" });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || "Could not delete file.");
    renderUploadStatus({ title: `${filename} removed`, detail: data.message || "", tone: "success" });
    showToast(data.message || "File deleted.");
  } catch (err) {
    renderUploadStatus({ title: "Delete failed", detail: err.message, tone: "error" });
    showToast(err.message);
  } finally {
    setPendingFile(filename, null);
    await loadUploadedFiles();
    loadAdminStats();
    setTimeout(() => renderUploadStatus(null), 6000);
  }
}

"""

# --------------------------------------------------------------------------
# backend/main.py
# --------------------------------------------------------------------------

PY_SUP_OLD = r'''    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 50))

    conn = get_db_connection()
    cursor = conn.cursor()

    show_disabled = _is_admin_request()

    where_sql = "WHERE functionary_type LIKE '%Supervisor%'"
    params = []
    if q:
        where_sql += " AND (name LIKE ? OR user_id LIKE ? OR mobile_number LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if not show_disabled:
        where_sql += " AND (status IS NULL OR UPPER(status) = 'ACTIVE')"

    cursor.execute(f"""
        SELECT * FROM functionaries {where_sql} ORDER BY name ASC LIMIT ?
    """, params + [limit])
    sup_rows = cursor.fetchall()'''

PY_SUP_NEW = r'''    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 50))

    conn = get_db_connection()
    cursor = conn.cursor()

    show_disabled = _is_admin_request()

    where_sql = "WHERE f.functionary_type LIKE '%Supervisor%'"
    params = []
    if q:
        clauses = ["f.name LIKE ?", "f.user_id LIKE ?", "f.mobile_number LIKE ?"]
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

        # Supervisory-circle lookup. Circle numbers live in hlb_allocations,
        # not functionaries, so a plain name/ID/mobile search could never
        # match one. The sheets also pad them inconsistently ("5", "05",
        # "005"), so match on the numeric value as well as the common
        # zero-padded literals.
        q_digits = re.sub(r'\D', '', q)
        if q_digits and int(q_digits) > 0:
            clauses.append("""EXISTS (
                SELECT 1 FROM hlb_allocations h
                WHERE (h.supervisor_name = f.name OR h.supervisor_name LIKE '%' || f.name || '%')
                  AND h.supervisory_circle_no IS NOT NULL
                  AND TRIM(h.supervisory_circle_no) != ''
                  AND (
                        CAST(h.supervisory_circle_no AS INTEGER) = ?
                     OR TRIM(h.supervisory_circle_no) IN (?, ?, ?, ?)
                  )
            )""")
            n = int(q_digits)
            params.extend([n, str(n), str(n).zfill(2), str(n).zfill(3), str(n).zfill(4)])

        where_sql += " AND (" + " OR ".join(clauses) + ")"

    if not show_disabled:
        where_sql += " AND (f.status IS NULL OR UPPER(f.status) = 'ACTIVE')"

    cursor.execute(f"""
        SELECT f.* FROM functionaries f {where_sql} ORDER BY f.name ASC LIMIT ?
    """, params + [limit])
    sup_rows = cursor.fetchall()'''

PY_ENUM_SELECT_OLD = (
    "            SELECT h.hlb_no, h.supervisory_circle_no, h.enumerator_name, "
    "h.enumerator_user_id, h.allotment_date,"
)
PY_ENUM_SELECT_NEW = (
    "            SELECT h.hlb_no, h.supervisory_circle_no, h.supervisor_name, h.enumerator_name,\n"
    "                   h.enumerator_user_id, h.allotment_date,"
)


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------

class Edit:
    """One anchored replacement. `marker` detects an already-applied edit."""

    def __init__(self, label, old, new, marker=None):
        self.label = label
        self.old = old
        self.new = new
        self.marker = marker if marker is not None else new

    def apply(self, text):
        """Return (new_text, status) where status is applied/skipped/missing.

        The marker is checked FIRST: some edits (e.g. inserting a sibling
        div) leave their own anchor intact, so an anchor-first check would
        re-apply them on every run.
        """
        if self.marker in text:
            return text, "skipped"
        if self.old in text:
            return text.replace(self.old, self.new, 1), "applied"
        return text, "missing"


class SpliceEdit(Edit):
    """Replaces everything from `start` up to (not including) `end`."""

    def __init__(self, label, start, end, new, marker):
        super().__init__(label, start, new, marker)
        self.end = end

    def apply(self, text):
        if self.marker in text:
            return text, "skipped"
        i = text.find(self.old)
        j = text.find(self.end)
        if i == -1 or j == -1 or j < i:
            return text, "missing"
        return text[:i] + self.new + text[j:], "applied"


PLAN = {
    os.path.join("frontend", "index.html"): [
        Edit("home: drop Ask AI tile, grid 4->3 cols",
             HTML_QUICK_ACTIONS_OLD, HTML_QUICK_ACTIONS_NEW,
             marker='grid grid-cols-2 sm:grid-cols-3 gap-3'),
        Edit("home: search placeholder now records-oriented",
             HTML_HOME_PLACEHOLDER_OLD, HTML_HOME_PLACEHOLDER_NEW),
        Edit("supervisor: search placeholder mentions circle no.",
             HTML_SUP_PLACEHOLDER_OLD, HTML_SUP_PLACEHOLDER_NEW),
        Edit("admin: id on Excel dropzone",
             HTML_EXCEL_DROPZONE_OLD, HTML_EXCEL_DROPZONE_NEW,
             marker='id="excel-dropzone"'),
        Edit("admin: id on PDF dropzone",
             HTML_PDF_DROPZONE_OLD, HTML_PDF_DROPZONE_NEW,
             marker='id="pdf-dropzone"'),
        Edit("admin: upload status box",
             HTML_STATUS_BOX_OLD, HTML_STATUS_BOX_NEW,
             marker='id="admin-upload-status"'),
    ],
    os.path.join("frontend", "app.js"): [
        Edit("i18n: en search placeholder", *JS_PLACEHOLDERS[0]),
        Edit("i18n: as search placeholder", *JS_PLACEHOLDERS[1]),
        Edit("i18n: hi search placeholder", *JS_PLACEHOLDERS[2]),
        Edit("i18n: bn search placeholder", *JS_PLACEHOLDERS[3]),
        Edit("state: pendingFiles / uploadInFlight",
             JS_STATE_OLD, JS_STATE_NEW, marker="uploadInFlight: false"),
        Edit("executeHomeSearch -> records search",
             JS_HOME_SEARCH_OLD, JS_HOME_SEARCH_NEW,
             marker='navigateTo("search");   // navigateTo() resets'),
        SpliceEdit("admin: upload/delete status handlers",
                   JS_UPLOAD_START, JS_UPLOAD_END, JS_UPLOAD_NEW,
                   marker="function uploadWithProgress("),
    ],
    os.path.join("backend", "main.py"): [
        Edit("supervisor_list: match supervisory circle number",
             PY_SUP_OLD, PY_SUP_NEW, marker="Supervisory-circle lookup"),
        Edit("supervisor_list: select h.supervisor_name for enumerators",
             PY_ENUM_SELECT_OLD, PY_ENUM_SELECT_NEW,
             marker="SELECT h.hlb_no, h.supervisory_circle_no, h.supervisor_name, h.enumerator_name,"),
    ],
}


def revert(root):
    restored = 0
    for rel in PLAN:
        path = os.path.join(root, rel)
        bak = path + ".bak"
        if os.path.exists(bak):
            shutil.copyfile(bak, path)
            os.remove(bak)
            print(f"  restored {rel}")
            restored += 1
    print(f"\nReverted {restored} file(s)." if restored else "\nNo .bak files found.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository root (default: .)")
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--revert", action="store_true", help="restore from .bak files")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    print(f"Census Assistant fixes — {root}\n")

    if args.revert:
        return revert(root)

    missing_files = [r for r in PLAN if not os.path.exists(os.path.join(root, r))]
    if missing_files:
        print("ERROR: not a Census Assistant checkout — missing:")
        for r in missing_files:
            print(f"  {r}")
        print("\nRun this from the repository root, or pass --root /path/to/repo")
        return 1

    results = {}
    failures = []

    for rel, edits in PLAN.items():
        path = os.path.join(root, rel)
        with open(path, encoding="utf-8") as fh:
            original = fh.read()
        text = original
        print(rel)
        for edit in edits:
            text, status = edit.apply(text)
            symbol = {"applied": "  +", "skipped": "  =", "missing": "  !"}[status]
            note = {"applied": "", "skipped": "  (already applied)",
                    "missing": "  ANCHOR NOT FOUND"}[status]
            print(f"{symbol} {edit.label}{note}")
            if status == "missing":
                failures.append(f"{rel}: {edit.label}")
        results[path] = (original, text)
        print()

    if failures:
        print("ABORTED — nothing was written. Could not locate:")
        for f in failures:
            print(f"  {f}")
        print("\nThese files have drifted from the reviewed versions. Apply "
              "those edits by hand, or reset the files and re-run.")
        return 1

    changed = [p for p, (o, n) in results.items() if o != n]
    if not changed:
        print("All three fixes are already applied. Nothing to do.")
        return 0

    if args.check:
        print(f"--check: {len(changed)} file(s) would be modified. Nothing written.")
        return 0

    for path in changed:
        original, new = results[path]
        bak = path + ".bak"
        if not os.path.exists(bak):
            with open(bak, "w", encoding="utf-8") as fh:
                fh.write(original)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)
        print(f"wrote {os.path.relpath(path, root)}  (backup: {os.path.basename(bak)})")

    print("\nDone. Next:")
    print("  python -m unittest tests.test_backend   # test_07 / test_12 cover the supervisor endpoint")
    print("  git diff")
    print("  git add -A && git commit -m 'Remove homepage Ask AI, circle-number supervisor search, live admin upload status'")
    print("  git push")
    print("\nThe .bak files are not gitignored — delete them before committing:")
    print("  rm frontend/*.bak backend/*.bak")
    return 0


if __name__ == "__main__":
    sys.exit(main())
