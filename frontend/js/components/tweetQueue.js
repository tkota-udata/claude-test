import { api } from "../api.js";
import { showToast, formatDate } from "../utils.js";

let refreshInterval = null;

export async function loadQueue() {
  const tbody = document.getElementById("queue-body");
  const header = document.getElementById("queue-header");

  try {
    const data = await api.scheduleList();
    const items = data.scheduled;
    header.textContent = `スケジュール済みツイート (${items.length}件)`;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty-state">スケジュールはありません</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    items.forEach((item) => {
      const tr = document.createElement("tr");

      const contentTd = document.createElement("td");
      contentTd.className = "queue-content";
      contentTd.textContent =
        item.content.length > 60 ? item.content.slice(0, 60) + "…" : item.content;
      contentTd.title = item.content;

      const dateTd = document.createElement("td");
      dateTd.textContent = formatDate(item.scheduled_at);

      const statusTd = document.createElement("td");
      statusTd.textContent = item.status;

      const actionTd = document.createElement("td");

      const postNowBtn = document.createElement("button");
      postNowBtn.className = "btn btn-primary btn-sm";
      postNowBtn.textContent = "今すぐ投稿";
      postNowBtn.addEventListener("click", async () => {
        postNowBtn.disabled = true;
        try {
          const result = await api.postScheduledNow(item.job_id);
          showToast(`投稿しました！ ${result.url}`, "success");
          await loadQueue();
        } catch (e) {
          showToast(`投稿失敗: ${e.message}`, "error");
          postNowBtn.disabled = false;
        }
      });

      const cancelBtn = document.createElement("button");
      cancelBtn.className = "btn btn-danger btn-sm";
      cancelBtn.textContent = "キャンセル";
      cancelBtn.addEventListener("click", async () => {
        try {
          await api.cancelSchedule(item.job_id);
          showToast("キャンセルしました", "info");
          await loadQueue();
        } catch (e) {
          showToast(`キャンセル失敗: ${e.message}`, "error");
        }
      });

      actionTd.appendChild(postNowBtn);
      actionTd.appendChild(cancelBtn);

      tr.appendChild(contentTd);
      tr.appendChild(dateTd);
      tr.appendChild(statusTd);
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">読み込み失敗: ${e.message}</td></tr>`;
  }
}

export function startQueueRefresh() {
  loadQueue();
  refreshInterval = setInterval(loadQueue, 30000);
}

export function stopQueueRefresh() {
  if (refreshInterval) clearInterval(refreshInterval);
}
