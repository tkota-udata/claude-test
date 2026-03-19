// Update this to your actual Render URL after deployment
const API_BASE = "https://your-app.onrender.com/api/v1";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

export const api = {
  health: () => apiFetch("/health"),
  generateTweets: (goal, context, count) =>
    apiFetch("/tweets/generate", {
      method: "POST",
      body: JSON.stringify({ goal, context, count }),
    }),
  postNow: (content) =>
    apiFetch("/tweets/post", {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  scheduleList: () => apiFetch("/schedule"),
  scheduleTweet: (content, scheduled_at) =>
    apiFetch("/schedule", {
      method: "POST",
      body: JSON.stringify({ content, scheduled_at }),
    }),
  cancelSchedule: (job_id) =>
    apiFetch(`/schedule/${job_id}`, { method: "DELETE" }),
};
