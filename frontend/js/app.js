import { api } from "./api.js";
import { showToast, setLoading } from "./utils.js";
import { initGoalForm } from "./components/goalForm.js";
import { renderTweetCards } from "./components/tweetGenerator.js";
import { loadQueue, startQueueRefresh } from "./components/tweetQueue.js";
import { initAutoPost } from "./components/autoPost.js";

async function checkHealth() {
  const indicator = document.getElementById("health-indicator");
  try {
    await api.health();
    indicator.className = "health-dot healthy";
    indicator.title = "バックエンド: 正常";
  } catch {
    indicator.className = "health-dot unhealthy";
    indicator.title = "バックエンド: 接続できません（スリープ中かもしれません）";
  }
}

async function handleGenerate({ goal, context, count }) {
  setLoading(true);
  try {
    const data = await api.generateTweets(goal, context, count);
    renderTweetCards(data.tweets, loadQueue);
  } catch (e) {
    showToast(`生成失敗: ${e.message}`, "error");
  } finally {
    setLoading(false);
  }
}

function requireAuth() {
  if (sessionStorage.getItem("auth") === "1") return;
  document.body.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0f1923;">
      <div style="background:#1a2634;padding:40px;border-radius:12px;border:1px solid #2f3336;text-align:center;width:320px;">
        <h2 style="color:#e7e9ea;margin-bottom:24px;">X 投稿自動化ツール</h2>
        <input id="pin-input" type="password" placeholder="パスワードを入力"
          style="width:100%;padding:12px;background:#0d1b27;border:1px solid #2f3336;border-radius:8px;color:#e7e9ea;font-size:1rem;margin-bottom:12px;" />
        <button id="pin-btn"
          style="width:100%;padding:12px;background:#1d9bf0;border:none;border-radius:8px;color:#fff;font-size:1rem;cursor:pointer;">
          ログイン
        </button>
        <p id="pin-error" style="color:#e0245e;margin-top:12px;min-height:20px;"></p>
      </div>
    </div>`;
  function tryLogin() {
    if (document.getElementById("pin-input").value === "testtest") {
      sessionStorage.setItem("auth", "1");
      location.reload();
    } else {
      document.getElementById("pin-error").textContent = "パスワードが違います";
    }
  }
  document.getElementById("pin-btn").addEventListener("click", tryLogin);
  document.getElementById("pin-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") tryLogin();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();
  checkHealth();
  initGoalForm(handleGenerate);
  initAutoPost();
  startQueueRefresh();

  document.getElementById("refresh-queue").addEventListener("click", loadQueue);
});
