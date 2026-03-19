import { showToast, setLoading } from "../utils.js";
import { api } from "../api.js";
import { renderSchedulePanel } from "./scheduler.js";

export function renderTweetCards(tweets, onScheduled) {
  const container = document.getElementById("tweet-cards");
  container.innerHTML = "";

  tweets.forEach((tweet) => {
    const card = document.createElement("div");
    card.className = "tweet-card";
    card.dataset.jobId = tweet.id;

    const textEl = document.createElement("div");
    textEl.className = "tweet-text";
    textEl.contentEditable = "true";
    textEl.textContent = tweet.content;

    const counter = document.createElement("div");
    counter.className = "char-counter";
    counter.textContent = `${tweet.content.length}/280`;

    textEl.addEventListener("input", () => {
      const len = textEl.textContent.length;
      counter.textContent = `${len}/280`;
      counter.classList.toggle("over-limit", len > 280);
    });

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const postBtn = document.createElement("button");
    postBtn.className = "btn btn-primary";
    postBtn.textContent = "今すぐ投稿";
    postBtn.addEventListener("click", async () => {
      const content = textEl.textContent.trim();
      if (content.length > 280) {
        showToast("280文字以内にしてください", "error");
        return;
      }
      setLoading(true);
      try {
        const result = await api.postNow(content);
        showToast(`投稿しました！ ${result.url}`, "success");
        card.classList.add("posted");
        postBtn.disabled = true;
      } catch (e) {
        showToast(`投稿失敗: ${e.message}`, "error");
      } finally {
        setLoading(false);
      }
    });

    const scheduleBtn = document.createElement("button");
    scheduleBtn.className = "btn btn-secondary";
    scheduleBtn.textContent = "スケジュール";
    scheduleBtn.addEventListener("click", () => {
      const existing = card.querySelector(".schedule-panel");
      if (existing) {
        existing.remove();
      } else {
        const panel = renderSchedulePanel(textEl, onScheduled);
        card.appendChild(panel);
      }
    });

    actions.appendChild(postBtn);
    actions.appendChild(scheduleBtn);

    card.appendChild(textEl);
    card.appendChild(counter);
    card.appendChild(actions);
    container.appendChild(card);
  });

  document.getElementById("tweets-section").style.display = "block";
}
