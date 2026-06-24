"use strict";

/* ===========================================================================
 * Config & persistent store
 * ======================================================================== */
const DEFAULT_API_BASE = "https://fastapi-social-media-api-yom4.onrender.com";
const API_PREFIX = "/api/v1"; // all routes are mounted under this prefix

const store = {
  get apiBase() { return DEFAULT_API_BASE; }, // fixed to the deployed backend; not user-configurable
  get token() { return localStorage.getItem("token"); },
  set token(v) { v ? localStorage.setItem("token", v) : localStorage.removeItem("token"); },
  get userId() { return Number(localStorage.getItem("userId")) || null; },
  set userId(v) { v ? localStorage.setItem("userId", v) : localStorage.removeItem("userId"); },
  get email() { return localStorage.getItem("email") || ""; },
  set email(v) { v ? localStorage.setItem("email", v) : localStorage.removeItem("email"); },
  get theme() { return localStorage.getItem("theme") || "dark"; },
  set theme(v) { localStorage.setItem("theme", v); },
};

/* ===========================================================================
 * DOM & formatting helpers
 * ======================================================================== */
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str ?? "";
  return d.innerHTML;
}

function initials(email) {
  return (email || "?").slice(0, 2).toUpperCase();
}

// Deterministic hue from a string → stable gradient identity per user.
function hueFor(str) {
  let h = 0;
  for (const ch of String(str || "")) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return h;
}
function avatarStyle(email) {
  const h = hueFor(email);
  return `background:linear-gradient(135deg,hsl(${h} 68% 56%),hsl(${(h + 38) % 360} 68% 46%))`;
}
// Markup for inline avatars inside string-built cards.
function avatarHTML(email, cls = "avatar-sm") {
  return `<span class="avatar ${cls}" style="${avatarStyle(email)}">${initials(email)}</span>`;
}
// Apply an avatar to an existing element (buttons in the shell).
function paintAvatar(node, email) {
  if (!node) return;
  node.setAttribute("style", avatarStyle(email));
  node.textContent = initials(email);
}

function timeAgo(iso) {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const s = Math.floor((Date.now() - then) / 1000);
  if (s < 60) return "just now";
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function fullDate(iso) {
  try { return new Date(iso).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" }); }
  catch { return iso; }
}

let toastTimer;
function toast(message, kind = "ok") {
  const t = $("#toast");
  t.textContent = message;
  t.className = `toast ${kind}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 3000);
}

/* ===========================================================================
 * API layer
 * ======================================================================== */
async function api(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  if (auth && store.token) headers["Authorization"] = `Bearer ${store.token}`;

  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(store.apiBase + API_PREFIX + path, { method, headers, body: payload });
  } catch {
    const e = new Error("Network error — is the API reachable?");
    e.status = 0;
    throw e;
  }

  if (res.status === 401) {
    logout();
    const e = new Error("Session expired. Please log in again.");
    e.status = 401;
    throw e;
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) {
        detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(", ") : data.detail;
      }
    } catch { /* keep default */ }
    const e = new Error(detail);
    e.status = res.status;
    throw e;
  }

  return res.status === 204 ? null : res.json();
}

/* ===========================================================================
 * Auth
 * ======================================================================== */
function decodeJwt(token) {
  try {
    const p = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(p));
  } catch { return {}; }
}

async function login(email, password) {
  const data = await api("/auth/login", { method: "POST", form: { username: email, password }, auth: false });
  store.token = data.access_token;
  store.email = email;
  store.userId = decodeJwt(data.access_token).user_id ?? null;
}

async function register(email, password) {
  await api("/auth/register", { method: "POST", body: { email, password }, auth: false });
}

function logout() {
  store.token = null;
  store.userId = null;
  store.email = null;
  $("#user-dropdown")?.classList.add("hidden");
  showAuthView();
}

/* ===========================================================================
 * View shell switching
 * ======================================================================== */
function showAuthView() {
  $("#app-view").classList.add("hidden");
  $("#auth-view").classList.remove("hidden");
  checkHealth(); // updates the hero pill too
}

function showAppView() {
  $("#auth-view").classList.add("hidden");
  $("#app-view").classList.remove("hidden");
  paintAvatar($("#avatar-btn"), store.email);
  paintAvatar($("#side-avatar"), store.email);
  paintAvatar($("#dropdown-avatar"), store.email);
  $("#dropdown-email").textContent = store.email;
  $("#side-email").textContent = store.email;
  checkHealth();
  if (!location.hash) location.hash = "#/feed";
  else router();
}

/* ===========================================================================
 * Reusable components
 * ======================================================================== */
// `post` is the flattened API object: { id, title, content, published,
// owner_id, created_at, votes, voted, owner? }. The feed/detail endpoints
// include `owner`; the profile endpoint's posts don't, so the caller injects it.
function postCard(post, { clickable = true, clamp = true } = {}) {
  const mine = post.owner_id === store.userId;

  const node = el(`
    <article class="post ${clickable ? "clickable" : ""}">
      <div class="post-head">
        ${avatarHTML(post.owner?.email)}
        <div>
          <a href="#/user/${post.owner_id}" class="post-author" data-stop>${escapeHtml(post.owner?.email || "unknown")}</a>
          <div class="post-time">${timeAgo(post.created_at)}</div>
        </div>
      </div>
      <h3 class="post-title">${escapeHtml(post.title)}</h3>
      <p class="post-content ${clamp ? "clamp" : ""}">${escapeHtml(post.content)}</p>
      <div class="post-foot">
        <button class="btn btn-sm vote-btn ${post.voted ? "voted" : ""}" data-vote>
          <span class="arr">▲</span> <span data-count>${post.votes}</span>
        </button>
        ${post.published ? "" : '<span class="draft-badge">Draft</span>'}
        <span class="spacer"></span>
        ${mine ? `<button class="btn btn-sm btn-ghost" data-edit>Edit</button>
                  <button class="btn btn-sm btn-danger" data-delete>Delete</button>` : ""}
      </div>
    </article>
  `);

  // Optimistic vote toggle (stops card navigation).
  $("[data-vote]", node).addEventListener("click", (e) => {
    e.stopPropagation();
    toggleVote(post, node);
  });
  // Author link shouldn't also trigger card navigation.
  $("[data-stop]", node).addEventListener("click", (e) => e.stopPropagation());
  if (mine) {
    $("[data-edit]", node).addEventListener("click", (e) => { e.stopPropagation(); openEditModal(post); });
    $("[data-delete]", node).addEventListener("click", (e) => { e.stopPropagation(); deletePost(post.id); });
  }
  if (clickable) node.addEventListener("click", () => { location.hash = `#/post/${post.id}`; });
  return node;
}

function skeletons(n = 3) {
  return Array.from({ length: n }, () => '<div class="skeleton skeleton-post"></div>').join("");
}

function emptyState(icon, title, text = "") {
  return `<div class="empty">
    <span class="empty-icon">${icon}</span>
    <div class="empty-title">${escapeHtml(title)}</div>
    ${text ? `<div>${escapeHtml(text)}</div>` : ""}
  </div>`;
}

function setView(html) {
  const root = $("#view-root");
  root.innerHTML = html;
  root.classList.remove("view-anim");
  void root.offsetWidth; // restart animation
  root.classList.add("view-anim");
}

/* ===========================================================================
 * Router
 * ======================================================================== */
const DETAIL_ROUTES = new Set(["post", "user"]);

function router() {
  if (!store.token) return showAuthView();
  const parts = location.hash.replace(/^#\/?/, "").split("/");
  const route = parts[0] || "feed";
  const param = parts[1];

  // Highlight active nav (sidebar + bottom nav).
  $$("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === route));
  // Mobile back button only on detail views.
  $("#mobile-back").classList.toggle("hidden", !DETAIL_ROUTES.has(route));

  switch (route) {
    case "feed": return renderFeed();
    case "create": return renderCreate();
    case "explore": return renderExplore();
    case "settings": return renderSettings();
    case "profile": return renderProfile(store.userId, true);
    case "post": return renderPostDetail(param);
    case "user": return renderProfile(Number(param), Number(param) === store.userId);
    default: location.hash = "#/feed";
  }
}

/* ===========================================================================
 * Feed view
 * ======================================================================== */
const feedState = { skip: 0, search: "", sort: "top", items: [], pageSize: 10 };

function renderFeed() {
  feedState.skip = 0;
  feedState.items = [];
  setView(`
    <div class="page-head">
      <div><h1 class="page-title">Feed</h1><p class="page-sub">Latest posts from the community</p></div>
      <a href="#/create" class="btn btn-primary btn-sm">+ New post</a>
    </div>

    <div class="feed-toolbar">
      <div class="search-wrap">
        <span class="search-ic">🔍</span>
        <input id="search-input" class="search" type="search" placeholder="Search posts by title or content…" value="${escapeHtml(feedState.search)}" />
      </div>
      <div class="sort-group">
        <button data-sort="top" class="${feedState.sort === "top" ? "active" : ""}">Top</button>
        <button data-sort="new" class="${feedState.sort === "new" ? "active" : ""}">Newest</button>
      </div>
    </div>

    <section id="feed" class="feed">${skeletons()}</section>
    <div id="load-more-wrap" class="load-more"></div>
  `);

  $("#search-input").addEventListener("input", debounceSearch);
  $$("[data-sort]").forEach((b) =>
    b.addEventListener("click", () => {
      if (feedState.sort === b.dataset.sort) return;
      feedState.sort = b.dataset.sort;
      feedState.skip = 0;
      feedState.items = [];
      $$("[data-sort]").forEach((x) => x.classList.toggle("active", x === b));
      loadFeed(true); // server re-orders the whole list
    })
  );

  loadFeed(true);
}

let searchTimer;
function debounceSearch(e) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    feedState.search = e.target.value.trim();
    feedState.skip = 0;
    feedState.items = [];
    loadFeed(true);
  }, 300);
}

async function loadFeed(fresh = false) {
  const feed = $("#feed");
  if (fresh) feed.innerHTML = skeletons();
  try {
    const q = new URLSearchParams({ sort: feedState.sort, limit: String(feedState.pageSize), skip: String(feedState.skip), search: feedState.search });
    const page = await api(`/posts/?${q}`);
    feedState.items = fresh ? page : feedState.items.concat(page);
    feedState.lastPageCount = page.length;
    renderItems();
  } catch (e) {
    feed.innerHTML = emptyState("⚠️", "Couldn't load the feed", e.message);
    $("#load-more-wrap").innerHTML = "";
  }
}

function renderItems() {
  const feed = $("#feed");
  const items = feedState.items; // already ordered by the server (sort=top|new)
  feed.innerHTML = "";
  if (!items.length) {
    feed.innerHTML = feedState.search
      ? emptyState("🔍", "No matches", `Nothing matches “${feedState.search}”.`)
      : emptyState("📭", "No posts yet", "Be the first to share something.");
    $("#load-more-wrap").innerHTML = "";
    return;
  }
  items.forEach((it) => feed.appendChild(postCard(it)));

  // Load-more if last page was full.
  const wrap = $("#load-more-wrap");
  if (feedState.lastPageCount === feedState.pageSize) {
    wrap.innerHTML = '<button class="btn btn-ghost" id="load-more-btn">Load more</button>';
    $("#load-more-btn").addEventListener("click", () => { feedState.skip += feedState.pageSize; loadFeed(false); });
  } else {
    wrap.innerHTML = "";
  }
}

/* ===========================================================================
 * Create post view
 * ======================================================================== */
function renderCreate() {
  setView(`
    <a href="#/feed" class="back-link">← Back to feed</a>
    <div class="page-head"><div><h1 class="page-title">Create a post</h1><p class="page-sub">Share something with the community</p></div></div>
    <section class="card composer">
      <form id="post-form">
        <input name="title" class="composer-title" placeholder="Post title" maxlength="120" required />
        <textarea name="content" placeholder="What's on your mind?" rows="8" required></textarea>
        <span class="char-count" data-count-for="content"></span>
        <div class="composer-actions">
          <label class="switch"><input type="checkbox" name="published" checked /><span class="switch-track"></span>Publish immediately</label>
          <button type="submit" class="btn btn-primary">Publish post</button>
        </div>
      </form>
    </section>
  `);
  wireCharCount($("#post-form textarea[name=content]"), 0);
  $("#post-form").addEventListener("submit", (e) => { e.preventDefault(); createPost(e.target); });
}

/* ===========================================================================
 * Post detail view
 * ======================================================================== */
async function renderPostDetail(id) {
  setView(`<a href="#/feed" class="back-link">← Back to feed</a><div class="skeleton skeleton-post"></div>`);
  try {
    const item = await api(`/posts/${id}`);
    setView(`<a href="#/feed" class="back-link">← Back to feed</a>`);
    $("#view-root").appendChild(postCard(item, { clickable: false, clamp: false }));
  } catch (e) {
    setView(`<a href="#/feed" class="back-link">← Back to feed</a>` + emptyState("⚠️", "Post unavailable", e.message));
  }
}

/* ===========================================================================
 * Profile view (own or another user's)
 * ======================================================================== */
async function renderProfile(userId, isMe) {
  setView(`<div class="skeleton skeleton-post" style="height:104px"></div>${skeletons(2)}`);
  try {
    // One call returns { user, posts }. Profile posts omit `owner`, so inject
    // the profile user as the owner for rendering/links.
    const { user, posts } = await api(isMe ? `/users/me` : `/users/${userId}`);
    const mine = posts.map((p) => ({ ...p, owner: user }));
    const votesReceived = mine.reduce((sum, it) => sum + it.votes, 0);

    setView(`
      <section class="card profile-card">
        <span class="avatar avatar-lg" style="${avatarStyle(user.email)}">${initials(user.email)}</span>
        <div class="profile-meta">
          <h2>${escapeHtml(user.email)}</h2>
          <p class="page-sub">Member since ${fullDate(user.created_at)}</p>
        </div>
      </section>
      <section class="stats">
        <div class="stat"><div class="stat-num">${mine.length}</div><div class="stat-label">Posts</div></div>
        <div class="stat"><div class="stat-num">${votesReceived}</div><div class="stat-label">Votes</div></div>
        <div class="stat"><div class="stat-num">#${user.id}</div><div class="stat-label">User&nbsp;ID</div></div>
      </section>
      <h3 class="section-label">${isMe ? "Your posts" : "Posts"}</h3>
      <section id="profile-feed" class="feed"></section>
    `);

    const feed = $("#profile-feed");
    if (!mine.length) {
      feed.innerHTML = emptyState("📝", isMe ? "No posts yet" : "Nothing here", isMe ? "Your published posts will show up here." : "This user hasn't posted yet.");
    } else {
      mine.forEach((it) => feed.appendChild(postCard(it)));
    }
  } catch (e) {
    setView(emptyState("⚠️", "Profile unavailable", e.message));
  }
}

/* ===========================================================================
 * Explore (users) view
 * ======================================================================== */
function renderExplore() {
  setView(`
    <div class="page-head"><div><h1 class="page-title">Explore</h1><p class="page-sub">People on SocialFeed</p></div></div>
    <form id="user-search" class="feed-toolbar">
      <div class="search-wrap">
        <span class="search-ic">🔍</span>
        <input id="user-search-input" class="search" type="search" placeholder="Search users by email…" />
      </div>
      <button type="submit" class="btn btn-primary">Search</button>
    </form>
    <section id="user-grid" class="user-grid">${skeletons(4)}</section>
  `);

  $("#user-search").addEventListener("submit", (e) => {
    e.preventDefault();
    loadUsers($("#user-search-input").value.trim());
  });

  loadUsers("");
}

async function loadUsers(search) {
  const grid = $("#user-grid");
  grid.innerHTML = skeletons(4);
  try {
    const q = new URLSearchParams({ limit: "100", search });
    const users = await api(`/users/?${q}`);
    grid.innerHTML = "";
    if (!users.length) {
      grid.innerHTML = emptyState("🔍", "No users found", search ? `Nothing matches “${search}”.` : "");
      return;
    }
    users.forEach((u) => {
      const card = el(`
        <article class="card user-card">
          ${avatarHTML(u.email)}
          <div>
            <div class="email">${escapeHtml(u.email)}</div>
            <div class="since">Joined ${timeAgo(u.created_at)}</div>
          </div>
        </article>
      `);
      card.addEventListener("click", () => { location.hash = `#/user/${u.id}`; });
      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = emptyState("⚠️", "Couldn't load users", e.message);
  }
}

/* ===========================================================================
 * Settings view (account, security, appearance, connection)
 * ======================================================================== */
function renderSettings() {
  setView(`
    <div class="page-head"><div><h1 class="page-title">Settings</h1><p class="page-sub">Manage your account and preferences</p></div></div>
    <div class="settings-stack">

      <section class="card settings-card">
        <h3>Account</h3>
        <p class="page-sub">You're signed in as</p>
        <div class="settings-row">
          <div style="display:flex;align-items:center;gap:0.75rem">
            ${avatarHTML(store.email, "")}
            <div><div class="label">${escapeHtml(store.email)}</div><div class="desc">User #${store.userId ?? "—"}</div></div>
          </div>
          <button id="settings-logout" class="btn btn-ghost btn-sm">Log out</button>
        </div>
      </section>

      <section class="card settings-card">
        <h3>Change password</h3>
        <p class="page-sub">Use a strong password you don't reuse elsewhere.</p>
        <form id="password-form" class="settings-form">
          <label class="field">Current password
            <input type="password" name="current_password" autocomplete="current-password" required />
          </label>
          <label class="field">New password <span class="hint">min 8 characters</span>
            <input type="password" name="new_password" minlength="8" autocomplete="new-password" required />
          </label>
          <label class="field">Confirm new password
            <input type="password" name="confirm_password" minlength="8" autocomplete="new-password" required />
          </label>
          <p id="password-msg" class="msg"></p>
          <div><button type="submit" class="btn btn-primary">Update password</button></div>
        </form>
      </section>

      <section class="card settings-card">
        <h3>Appearance</h3>
        <div class="settings-row">
          <div><div class="label">Dark theme</div><div class="desc">Switch between light and dark.</div></div>
          <label class="switch">
            <input type="checkbox" id="theme-switch" ${store.theme === "dark" ? "checked" : ""} />
            <span class="switch-track"></span>
          </label>
        </div>
      </section>

    </div>
  `);

  $("#settings-logout").addEventListener("click", logout);
  $("#password-form").addEventListener("submit", (e) => { e.preventDefault(); changePassword(e.target); });
  $("#theme-switch").addEventListener("change", (e) => applyTheme(e.target.checked ? "dark" : "light"));
}

async function changePassword(form) {
  const msg = $("#password-msg");
  msg.className = "msg";
  msg.textContent = "";
  const current_password = form.current_password.value;
  const new_password = form.new_password.value;
  const confirm_password = form.confirm_password.value;

  if (new_password !== confirm_password) { msg.textContent = "New and confirm password must match."; msg.className = "msg error"; return; }
  if (current_password === new_password) { msg.textContent = "New password must differ from the current one."; msg.className = "msg error"; return; }

  try {
    await api("/auth/change-password", { method: "PATCH", body: { current_password, new_password, confirm_password } });
    form.reset();
    msg.textContent = "Password updated successfully.";
    msg.className = "msg ok";
    toast("Password changed");
  } catch (e) {
    msg.textContent = e.message;
    msg.className = "msg error";
  }
}

/* ===========================================================================
 * Post actions
 * ======================================================================== */
async function createPost(form) {
  const fd = new FormData(form);
  const btn = $("button[type=submit]", form);
  btn.disabled = true;
  try {
    await api("/posts/", {
      method: "POST",
      body: { title: fd.get("title").trim(), content: fd.get("content").trim(), published: fd.get("published") === "on" },
    });
    form.reset();
    toast("Post published");
    feedState.skip = 0;
    feedState.search = "";
    if (location.hash === "#/feed") loadFeed(true);
    else location.hash = "#/feed";
  } catch (e) {
    toast(e.message, "error");
    btn.disabled = false;
  }
}

async function deletePost(id) {
  if (!confirm("Delete this post? This cannot be undone.")) return;
  try {
    await api(`/posts/${id}`, { method: "DELETE" });
    toast("Post deleted");
    router(); // re-render current view
  } catch (e) { toast(e.message, "error"); }
}

// Optimistic vote: update the card instantly, reconcile with the server after.
async function toggleVote(post, node) {
  const btn = $("[data-vote]", node);
  const countEl = $("[data-count]", node);
  const next = !post.voted;

  // Apply optimistic state.
  post.voted = next;
  post.votes += next ? 1 : -1;
  btn.classList.toggle("voted", next);
  countEl.textContent = post.votes;
  btn.classList.remove("vote-bump");
  void btn.offsetWidth;
  btn.classList.add("vote-bump");

  try {
    await api("/votes/", { method: "POST", body: { post_id: post.id, dir: next ? 1 : 0 } });
  } catch (e) {
    // 409 (already voted) / 404 (no vote to remove) just mean our view was stale —
    // the optimistic state already matches the server, so keep it. Otherwise revert.
    if (e.status !== 409 && e.status !== 404) {
      post.voted = !next;
      post.votes += next ? -1 : 1;
      btn.classList.toggle("voted", post.voted);
      countEl.textContent = post.votes;
      toast(e.message, "error");
    }
  }
}

/* ===========================================================================
 * Edit modal
 * ======================================================================== */
function openEditModal(post) {
  const f = $("#edit-form");
  f.id.value = post.id;
  f.title.value = post.title;
  f.content.value = post.content;
  f.published.checked = post.published;
  wireCharCount(f.content, 0);
  $("#edit-modal").classList.remove("hidden");
  f.title.focus();
}
function closeEditModal() { $("#edit-modal").classList.add("hidden"); }

async function saveEdit(form) {
  try {
    await api(`/posts/${form.id.value}`, {
      method: "PATCH",
      body: { title: form.title.value.trim(), content: form.content.value.trim(), published: form.published.checked },
    });
    closeEditModal();
    toast("Post updated");
    router();
  } catch (e) { toast(e.message, "error"); }
}

/* ===========================================================================
 * Char counter (composer + edit)
 * ======================================================================== */
function wireCharCount(textarea, max) {
  if (!textarea) return;
  const counter = textarea.parentElement.querySelector('.char-count[data-count-for="content"]')
    || document.querySelector('.char-count[data-count-for="content"]');
  if (!counter) return;
  const update = () => { counter.textContent = `${textarea.value.length} characters`; };
  textarea.addEventListener("input", update);
  update();
}

/* ===========================================================================
 * Health check
 * ======================================================================== */
async function checkHealth() {
  const dot = $("#health-dot");
  const pill = $("#hero-health");
  let ok = false;
  try { await api("/health", { auth: false }); ok = true; } catch { ok = false; }
  if (dot) { dot.className = `health-dot ${ok ? "ok" : "down"}`; dot.title = ok ? "API: connected" : "API: unavailable"; }
  if (pill) {
    pill.className = `pill ${ok ? "ok" : "down"}`;
    pill.innerHTML = `<span class="dot"></span> ${ok ? "API online" : "API unreachable"}`;
  }
}

/* ===========================================================================
 * Theme
 * ======================================================================== */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  $("#theme-toggle").textContent = theme === "dark" ? "🌙" : "☀️";
  const sw = $("#theme-switch");
  if (sw) sw.checked = theme === "dark";
  store.theme = theme;
}

/* ===========================================================================
 * Password strength meter (register form)
 * ======================================================================== */
function scorePassword(pw) {
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(s, 4);
}
function updatePwMeter(input) {
  const bar = input.closest(".field")?.querySelector("[data-pw-bar]");
  if (!bar) return;
  const score = input.value ? scorePassword(input.value) : 0;
  const colors = ["transparent", "var(--danger)", "var(--warn)", "var(--primary)", "var(--success)"];
  bar.style.width = `${(score / 4) * 100}%`;
  bar.style.background = colors[score];
}

/* ===========================================================================
 * Init / event wiring
 * ======================================================================== */
function init() {
  applyTheme(store.theme);

  // Auth segmented control.
  const seg = $(".seg");
  $$(".seg-btn").forEach((tab) =>
    tab.addEventListener("click", () => {
      $$(".seg-btn").forEach((t) => t.classList.remove("is-active"));
      tab.classList.add("is-active");
      const isLogin = tab.dataset.tab === "login";
      seg.dataset.active = tab.dataset.tab;
      $("#login-form").classList.toggle("hidden", !isLogin);
      $("#register-form").classList.toggle("hidden", isLogin);
      $("#auth-heading").textContent = isLogin ? "Welcome back" : "Create your account";
      $("#auth-subhead").textContent = isLogin ? "Sign in to continue to your feed." : "Join the community in seconds.";
      $("#auth-msg").textContent = "";
    })
  );

  // Show/hide password toggles.
  $$("[data-pw-toggle]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector("input");
      input.type = input.type === "password" ? "text" : "password";
      btn.style.opacity = input.type === "text" ? "1" : "";
    })
  );

  // Password strength meter on register.
  const regPw = $("#register-form input[name=password]");
  regPw?.addEventListener("input", () => updatePwMeter(regPw));

  $("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("#auth-msg"); msg.textContent = "Signing in…"; msg.className = "msg";
    const btn = $("button[type=submit]", e.target); btn.disabled = true;
    try { await login(e.target.email.value, e.target.password.value); showAppView(); }
    catch (err) { msg.textContent = err.message; msg.className = "msg error"; }
    finally { btn.disabled = false; }
  });

  $("#register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = $("#auth-msg"); msg.textContent = "Creating account…"; msg.className = "msg";
    const btn = $("button[type=submit]", e.target); btn.disabled = true;
    try {
      await register(e.target.email.value, e.target.password.value);
      await login(e.target.email.value, e.target.password.value);
      showAppView();
    } catch (err) { msg.textContent = err.message; msg.className = "msg error"; }
    finally { btn.disabled = false; }
  });

  // Theme toggle (topbar).
  $("#theme-toggle").addEventListener("click", () =>
    applyTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark")
  );

  // Mobile back button.
  $("#mobile-back").addEventListener("click", () => history.back());

  // Avatar dropdown + sidebar user → settings.
  $("#avatar-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    $("#user-dropdown").classList.toggle("hidden");
  });
  $("#side-user").addEventListener("click", () => { location.hash = "#/settings"; });
  document.addEventListener("click", () => $("#user-dropdown").classList.add("hidden"));
  $("#logout-btn").addEventListener("click", logout);

  // Edit modal.
  $("#edit-form").addEventListener("submit", (e) => { e.preventDefault(); saveEdit(e.target); });
  $("#edit-cancel").addEventListener("click", closeEditModal);
  $("#edit-close").addEventListener("click", closeEditModal);
  $("#edit-modal").addEventListener("click", (e) => { if (e.target.id === "edit-modal") closeEditModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeEditModal(); });

  // Routing.
  window.addEventListener("hashchange", router);

  if (store.token) showAppView();
  else showAuthView();
}

document.addEventListener("DOMContentLoaded", init);
