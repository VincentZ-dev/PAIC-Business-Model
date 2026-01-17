from flask import Flask, request, jsonify, render_template_string
from google import genai
from markdown import markdown
import json
import re
from google.genai.errors import ClientError


app = Flask(__name__)

# =========================================================
# 🔑 GEMINI API KEY
# =========================================================
API_KEY = "AIzaSyATihNPWSDSdgnkIm-ItPuTi0QBgcfcPOE"
client = genai.Client(api_key=API_KEY)
# =========================================================

conversation = []
business_snapshot = {}
ready_to_generate = False

# =========================
# MAIN PAGE (UPDATED DESIGN)
# =========================
MAIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Business Builder</title>
<style>
body { margin:0; font-family:Arial; height:100vh; display:flex; }
#left { width:50%; padding:30px; background:#00264D; overflow-y:auto; color:#FFFFFF; border-right:14px solid #FFFADA; }
#right { width:50%; display:flex; flex-direction:column; background:#d3cebe; color:#FFFFFF; }
#summary div { margin-bottom:14px; }
#chat { flex:1; padding:20px; overflow-y:auto; }
#inputBox { display:flex; padding:10px; background:#111; }
#inputBox input {
    flex:1;
    padding:10px;
    border:none;
    outline:none;
    color:#fff;
    background:#222;
}
#inputBox button {
    padding:0 15px;
    background:#0077ff;
    border:none;
    color:#fff;
    cursor:pointer;
    font-size:18px;
}
.bigPrompt { text-align:center; margin-top:40%; font-size:20px; opacity:.8; color:#FFFFFF; }
.smallPrompt { font-size:12px; opacity:.7; margin-bottom:10px; color:#FFFFFF; }
.msg-user { text-align:right; margin:10px; color:#00264D; }
.msg-ai { text-align:left; margin:10px; color:#144c8c; }
</style>
</head>

<body>
<div id="left">
<h2>Business Snapshot</h2>
<div id="summary"></div>
</div>

<div id="right">
<div id="chat">
<div id="prompt" class="bigPrompt">
<b>
  <span style="color: #000000;">
    Tell me about the ideas you have for your business
  </span>
</b><br><br>
<span style="font-size:14px; color:#000000;">
Once you're finished, tell me "That's all" or "I'm finished".
</span>
</div>
</div>

<div id="inputBox">
    <input id="input" placeholder="Type here..." onkeydown="handleKey(event)" />
    <button onclick="send()">↑</button>
</div>
</div>

<script>
let firstMessage = true;

function handleKey(e) {
    if (e.key === "Enter") {
        e.preventDefault();
        send();
    }
}

function send(){
    const input = document.getElementById("input");
    if (!input.value.trim()) return;

    if (firstMessage){
        document.getElementById("prompt").className = "smallPrompt";
        document.getElementById("prompt").style.marginTop = "0";
        firstMessage = false;
    }

    addMsg("msg-user", input.value);

    fetch("/chat",{
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body:JSON.stringify({ text: input.value })
    })
    .then(r => r.json())
    .then(d => {
        addMsg("msg-ai", d.reply);
        updateSummary(d.snapshot);
        if (d.redirect) window.location.href = "/result";
    });

    input.value = "";
}

function addMsg(cls,text){
    let d=document.createElement("div");
    d.className=cls;
    d.innerText=text;
    document.getElementById("chat").appendChild(d);
    document.getElementById("chat").scrollTop = document.getElementById("chat").scrollHeight;
}

function updateSummary(data){
    const s=document.getElementById("summary");
    s.innerHTML="";
    Object.keys(data).forEach(k=>{
        let d=document.createElement("div");
        d.innerHTML = "<b>"+k+":</b> "+data[k];
        s.appendChild(d);
    });
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(MAIN_PAGE)

# =========================
# CHAT ROUTE (AI — UNCHANGED)
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    global conversation, business_snapshot, ready_to_generate

    user_text = request.json["text"]
    conversation.append(f"User: {user_text}")

    SYSTEM_PROMPT = """
You are an intelligent business consultant.

Your goals:
- Understand the user's intent.
- Answer questions clearly if asked.
- Extract business information naturally.
- Decide if the user is finished and ready to generate.

IMPORTANT RULES FOR BUSINESS SNAPSHOT:
- Do NOT duplicate information across fields.
- "Location" = specific city or local area.
- "Region" = broader geographic scope.
- Never repeat the same value for both.

Respond ONLY with valid JSON:
{
  "chat_reply": "string",
  "business_snapshot": { "Field": "Value" },
  "ready_to_generate": true or false
}
"""

    prompt = SYSTEM_PROMPT + "\n\nConversation:\n" + "\n".join(conversation)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
    except ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            return jsonify({
                "reply": "⚠️ API quota reached. Please wait about 1 minute and try again.",
                "snapshot": business_snapshot,
                "redirect": False
            })
        raise e

    match = re.search(r"\{.*\}", response.text, re.S)
    if not match:
        return jsonify({
            "reply": "Sorry, could you rephrase that?",
            "snapshot": business_snapshot,
            "redirect": False
        })

    parsed = json.loads(match.group())

    business_snapshot.update(parsed.get("business_snapshot", {}))
    ready_to_generate = parsed.get("ready_to_generate", False)

    conversation.append(f"Assistant: {parsed['chat_reply']}")

    return jsonify({
        "reply": parsed["chat_reply"],
        "snapshot": business_snapshot,
        "redirect": ready_to_generate
    })

# =========================
# RESULT PAGE (UPGRADED)
# =========================
@app.route("/result")
def result():
    prompt = "Generate a realistic, real-world business plan using this data:\n"
    for k, v in business_snapshot.items():
        prompt += f"{k}: {v}\n"

    try:
        r = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
    except ClientError:
        return """
        <h2 style="color:red;text-align:center;">
            API quota reached.<br>
            Please wait a minute and refresh this page.
        </h2>
        """

    html_output = markdown(
        r.text,
        extensions=["fenced_code", "tables", "toc", "attr_list"]
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Business Model Result</title>
<style>
body {{
    margin:0;
    padding:24px;
    font-family:system-ui;
    background:linear-gradient(135deg,#144C8C,#00498D,#00264D);
}}
.card {{
    max-width:960px;
    margin:auto;
    background:#fff;
    border-radius:18px;
    padding:24px;
    box-shadow:0 12px 32px rgba(0,0,0,.35);
}}
.markdown-output h1,h2,h3 {{ color:#00498D; }}
.markdown-output pre {{
    background:#00264D;
    color:#fff;
    padding:14px;
    border-radius:10px;
}}
.markdown-output table {{
    width:100%;
    border-collapse:collapse;
}}
.markdown-output th,td {{
    border:1px solid #D3CEBE;
    padding:8px;
}}
</style>
</head>
<body>
<div class="card">
<div class="markdown-output">{html_output}</div>
<br>
<a href="/">← Start Over</a>
</div>
</body>
</html>
"""

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)

#color = '''Tan:d3cebe DarkBlue:144c8c 00498D 00264D Gold:FFCC00'''