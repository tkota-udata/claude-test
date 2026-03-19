export function initGoalForm(onGenerate) {
  const form = document.getElementById("goal-form");
  const goalInput = document.getElementById("goal-input");
  const contextInput = document.getElementById("context-input");
  const countInput = document.getElementById("count-input");

  // Restore saved goal
  const saved = localStorage.getItem("x_auto_goal");
  if (saved) goalInput.value = saved;

  goalInput.addEventListener("input", () => {
    localStorage.setItem("x_auto_goal", goalInput.value);
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const goal = goalInput.value.trim();
    if (!goal) return;
    onGenerate({
      goal,
      context: contextInput.value.trim(),
      count: parseInt(countInput.value, 10) || 3,
    });
  });
}
