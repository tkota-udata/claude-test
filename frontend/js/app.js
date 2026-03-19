import { api } from "./api.js";
import { showToast, setLoading } from "./utils.js";
import { initGoalForm } from "./components/goalForm.js";
import { renderTweetCards } from "./components/tweetGenerator.js";
import { loadQueue, startQueueRefresh } from "./components/tweetQueue.js";

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

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  initGoalForm(handleGenerate);
  startQueueRefresh();

  document.getElementById("refresh-queue").addEventListener("click", loadQueue);
});
