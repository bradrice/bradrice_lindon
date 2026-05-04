document.addEventListener("DOMContentLoaded", () => {
  const dateItem = document.getElementById("currentYear");
  const date = new Date();
  const year = date.getFullYear();
  dateItem.textContent = year;
});
