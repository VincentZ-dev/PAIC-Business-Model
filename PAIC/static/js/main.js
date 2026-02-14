// Main Page JavaScript

let firstMessage = true;

function handleKey(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    send();
  }
}

function setLoading(isLoading) {
  const input = document.getElementById('input');
  const btn = document.querySelector('#inputBox button');
  const chat = document.getElementById('chat');
  let typ = document.getElementById('typing');
  if (isLoading) {
    if (!typ) {
      typ = document.createElement('div');
      typ.id = 'typing';
      typ.className = 'msg-ai';
      const b = document.createElement('div');
      b.className = 'message';
      b.innerText = 'AI is thinking…';
      typ.appendChild(b);
      chat.appendChild(typ);
    }
    if (input) input.disabled = true;
    if (btn) btn.disabled = true;
    typ.style.display = 'flex';
    chat.scrollTop = chat.scrollHeight;
  } else {
    if (input) input.disabled = false;
    if (btn) btn.disabled = false;
    if (typ) typ.style.display = 'none';
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
  setLoading(true);

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: input.value })
  })
    .then(r => r.json())
    .then(d => {
      setLoading(false);
      addMsg("msg-ai", d.reply);
      updateSummary(d.snapshot);
      if (d.redirect) window.location.href = "/result";
    })
    .catch(err => {
      console.error("Error:", err);
      setLoading(false);
      addMsg("msg-ai", "Sorry, there was an error. Please try again.");
    });

  input.value = "";
}

function addMsg(cls, text) {
  const chat = document.getElementById("chat");
  let inner = document.getElementById('chatInner');
  if (!inner) {
    inner = document.createElement('div');
    inner.id = 'chatInner';
    // move existing children into inner
    while (chat.firstChild) inner.appendChild(chat.firstChild);
    chat.appendChild(inner);
  }

  let container = document.createElement("div");
  container.className = cls;
  let bubble = document.createElement('div');
  bubble.className = 'message';
  bubble.innerText = text;
  container.appendChild(bubble);
  inner.appendChild(container);

  // adjust scaling so content fits without scrolling
  adjustChatScale();
}

function adjustChatScale() {
  const chat = document.getElementById('chat');
  const inner = document.getElementById('chatInner');
  if (!chat || !inner) return;

  // reset transform to measure true height
  inner.style.transform = 'none';
  const containerH = chat.clientHeight;
  const innerH = inner.scrollHeight;

  // if content fits, ensure normal scale
  if (innerH <= containerH) {
    inner.style.transform = 'none';
    inner.dataset.scale = '1';
    return;
  }

  // compute scale (don't shrink below 0.6)
  let scale = containerH / innerH;
  const minScale = 0.6;
  if (scale < minScale) {
    scale = minScale;
  }

  inner.style.transform = `scale(${scale})`;
  inner.dataset.scale = String(scale);

  // If scale == minScale and still overflowing, remove oldest messages (simple strategy)
  if (scale === minScale && inner.scrollHeight * scale > containerH) {
    // remove first message until it fits or we've removed 3
    let removed = 0;
    while (inner.firstChild && removed < 3 && inner.scrollHeight * scale > containerH) {
      inner.removeChild(inner.firstChild);
      removed++;
    }
  }
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
