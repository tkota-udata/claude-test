import { api } from "../api.js";
import { showToast, setLoading } from "../utils.js";

export function renderSchedulePanel(textEl, onScheduled) {
  const panel = document.createElement("div");
  panel.className = "schedule-panel";

  const label = document.createElement("label");
  label.textContent = "投稿日時を選択";

  const input = document.createElement("input");
  input.type = "datetime-local";
  // Set min to now
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  input.min = now.toISOString().slice(0, 16);

  const confirmBtn = document.createElement("button");
  confirmBtn.className = "btn btn-accent";
  confirmBtn.textContent = "スケジュール確定";

  confirmBtn.addEventListener("click", async () => {
    const content = textEl.textContent.trim();
    if (!input.value) {
      showToast("日時を選択してください", "error");
      return;
    }
    if (content.length > 280) {
      showToast("280文字以内にしてください", "error");
      return;
    }

    // Convert local datetime to UTC ISO string
    const localDate = new Date(input.value);
    const utcIso = localDate.toISOString();

    setLoading(true);
    try {
      await api.scheduleTweet(content, utcIso);
      showToast("スケジュール登録しました！", "success");
      panel.remove();
      if (onScheduled) onScheduled();
    } catch (e) {
      showToast(`スケジュール失敗: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  });

  panel.appendChild(label);
  panel.appendChild(input);
  panel.appendChild(confirmBtn);
  return panel;
}
