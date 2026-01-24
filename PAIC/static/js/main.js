// Main Page JavaScript

let firstMessage = true;

function handleKey(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    send();
  }
}

function send() {
  const input = document.getElementById("input");
  if (!input.value.trim()) return;

  if (firstMessage) {
    document.getElementById("prompt").className = "smallPrompt";
    document.getElementById("prompt").style.marginTop = "0";
    firstMessage = false;
  }

  addMsg("msg-user", input.value);

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: input.value })
  })
    .then(r => r.json())
    .then(d => {
      addMsg("msg-ai", d.reply);
      updateSummary(d.snapshot);
      if (d.redirect) window.location.href = "/result";
    })
    .catch(err => {
      console.error("Error:", err);
      addMsg("msg-ai", "Sorry, there was an error. Please try again.");
    });

  input.value = "";
}

function addMsg(cls, text) {
  let d = document.createElement("div");
  d.className = cls;
  d.innerText = text;
  document.getElementById("chat").appendChild(d);
  document.getElementById("chat").scrollTop = document.getElementById("chat").scrollHeight;
}

function updateSummary(data) {
  const s = document.getElementById("summary");
  s.innerHTML = "";
  Object.keys(data).forEach(k => {
    let d = document.createElement("div");
    d.innerHTML = "<b>" + k + ":</b> " + data[k];
    s.appendChild(d);
  });
}
