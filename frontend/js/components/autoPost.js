import { api } from "../api.js";
import { showToast } from "../utils.js";

export async function initAutoPost() {
  document.getElementById("autopost-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const goal = document.getElementById("autopost-goal").value.trim();
    const times_per_day = parseInt(document.getElementById("autopost-times").value);
    const start_hour = parseInt(document.getElementById("autopost-start").value);
    const end_hour = parseInt(document.getElementById("autopost-end").value);

    if (!goal) return showToast("ゴールを入力してください", "error");
    if (start_hour >= end_hour) return showToast("開始時刻は終了時刻より前にしてください", "error");

    try {
      await api.createAutoPost({ goal, times_per_day, start_hour, end_hour });
      showToast("自動投稿スケジュールを設定しました");
      document.getElementById("autopost-goal").value = "";
      await loadAutoPostList();
    } catch (err) {
      showToast(`設定失敗: ${err.message}`, "error");
    }
  });

  await loadAutoPostList();
  await loadAnalytics();
}

async function loadAutoPostList() {
  const container = document.getElementById("autopost-list");
  try {
    const data = await api.listAutoPosts();
    if (!data.schedules.length) {
      container.innerHTML = '<p class="empty-state">自動投稿スケジュールはありません</p>';
      return;
    }
    container.innerHTML = data.schedules.map((s) => `
      <div class="autopost-item" data-id="${s.id}">
        <div class="autopost-info">
          <div class="autopost-goal-text">${escHtml(s.goal)}</div>
          <div class="autopost-meta">1日${s.times_per_day}回 &nbsp;|&nbsp; ${s.start_hour}:00〜${s.end_hour}:00</div>
        </div>
        <div class="autopost-actions">
          <label class="toggle-switch" title="${s.enabled ? '有効' : '無効'}">
            <input type="checkbox" class="toggle-enabled" ${s.enabled ? "checked" : ""} />
            <span class="toggle-slider"></span>
          </label>
          <button class="btn btn-danger btn-sm delete-autopost">削除</button>
        </div>
      </div>
    `).join("");

    container.querySelectorAll(".toggle-enabled").forEach((toggle) => {
      toggle.addEventListener("change", async (e) => {
        const id = e.target.closest(".autopost-item").dataset.id;
        try {
          await api.toggleAutoPost(id, e.target.checked);
          showToast(e.target.checked ? "有効にしました" : "無効にしました");
        } catch (err) {
          showToast(`変更失敗: ${err.message}`, "error");
          e.target.checked = !e.target.checked;
        }
      });
    });

    container.querySelectorAll(".delete-autopost").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const id = e.target.closest(".autopost-item").dataset.id;
        if (!confirm("自動投稿スケジュールを削除しますか？")) return;
        try {
          await api.deleteAutoPost(id);
          showToast("削除しました");
          await loadAutoPostList();
        } catch (err) {
          showToast(`削除失敗: ${err.message}`, "error");
        }
      });
    });
  } catch (err) {
    container.innerHTML = `<p class="empty-state">読み込みに失敗しました</p>`;
  }
}

async function loadAnalytics() {
  try {
    const data = await api.getAnalytics();
    const section = document.getElementById("analytics-section");

    if (data.follower_count > 0) {
      document.getElementById("follower-count").textContent =
        `フォロワー: ${data.follower_count.toLocaleString()}人`;
    }

    const list = document.getElementById("top-tweets-list");
    if (!data.top_tweets.length) {
      list.innerHTML = '<p class="empty-state">まだデータがありません（投稿後24時間で集計されます）</p>';
    } else {
      list.innerHTML = data.top_tweets.map((t) => `
        <div class="analytics-tweet">
          <div class="analytics-content">${escHtml(t.content)}</div>
          <div class="analytics-metrics">
            <span>いいね ${t.likes ?? 0}</span>
            <span>RT ${t.retweets ?? 0}</span>
            <span>返信 ${t.replies ?? 0}</span>
          </div>
        </div>
      `).join("");
    }
    section.style.display = "";
  } catch {
    // Keep analytics section hidden if unavailable
  }
}

function escHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
