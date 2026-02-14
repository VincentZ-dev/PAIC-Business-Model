from google import genai
from markdown import markdown
import json
import re
from google.genai.errors import ClientError


app = Flask(__name__)

# =========================================================
# 🔑 GEMINI API KEY
# =========================================================
API_KEY = "AIzaSyAPi78_IjFZunJLtq_-oYTnixB26RBX2U8"
client = genai.Client(api_key=API_KEY)
# =========================================================

conversation = []
business_snapshot = {}
ready_to_generate = False

# Directory to store generated documents

DOCUMENTS_DIR = "generated_documents"
LOGO_DIR = os.path.join("static", "generated_logos")
if not os.path.exists(DOCUMENTS_DIR):
    os.makedirs(DOCUMENTS_DIR)
if not os.path.exists(LOGO_DIR):
    os.makedirs(LOGO_DIR)

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
        if (d.redirect) window.location.href = "/loading";
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
# LOADING PAGE
# =========================
LOADING_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Generating Your Business Model...</title>
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    background: linear-gradient(135deg, #00264D 0%, #00498D 50%, #144C8C 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
}

.loader-container {
    text-align: center;
    color: #FFFFFF;
}

.loader-title {
    font-size: 28px;
    margin-bottom: 40px;
    animation: fadeInUp 0.8s ease-out;
}

.loader-subtitle {
    font-size: 16px;
    opacity: 0.8;
    margin-bottom: 50px;
    animation: fadeInUp 0.8s ease-out 0.2s both;
}

/* Spinning circles loader */
.spinner {
    position: relative;
    width: 100px;
    height: 100px;
    margin: 0 auto 40px;
}

.spinner-circle {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 4px solid transparent;
    border-radius: 50%;
    animation: spin 1.5s linear infinite;
}

.spinner-circle:nth-child(1) {
    border-top-color: #FFFADA;
    animation-delay: 0s;
}

.spinner-circle:nth-child(2) {
    width: 80%;
    height: 80%;
    top: 10%;
    left: 10%;
    border-right-color: #D3CEBE;
    animation-delay: 0.15s;
    animation-direction: reverse;
}

.spinner-circle:nth-child(3) {
    width: 60%;
    height: 60%;
    top: 20%;
    left: 20%;
    border-bottom-color: #FFFFFF;
    animation-delay: 0.3s;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Progress dots */
.progress-dots {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 30px;
}

.dot {
    width: 12px;
    height: 12px;
    background: #FFFADA;
    border-radius: 50%;
    animation: pulse 1.4s ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
.dot:nth-child(4) { animation-delay: 0.6s; }

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.4; }
    50% { transform: scale(1.3); opacity: 1; }
}

/* Status messages */
.status-message {
    font-size: 14px;
    opacity: 0.9;
    animation: statusFade 3s ease-in-out infinite;
}

@keyframes statusFade {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Floating particles background */
.particles {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: hidden;
    z-index: -1;
}

.particle {
    position: absolute;
    width: 6px;
    height: 6px;
    background: rgba(255, 250, 218, 0.3);
    border-radius: 50%;
    animation: float 15s infinite;
}

@keyframes float {
    0%, 100% {
        transform: translateY(100vh) rotate(0deg);
        opacity: 0;
    }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% {
        transform: translateY(-100vh) rotate(720deg);
        opacity: 0;
    }
}
</style>
</head>
<body>

<div class="particles" id="particles"></div>

<div class="loader-container">
    <h1 class="loader-title">Building Your Business Model</h1>
    <p class="loader-subtitle">Our AI is crafting a personalized plan just for you</p>
    
    <div class="spinner">
        <div class="spinner-circle"></div>
        <div class="spinner-circle"></div>
        <div class="spinner-circle"></div>
    </div>
    
    <div class="progress-dots">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    </div>
    
    <p class="status-message" id="statusMessage">Analyzing your business data...</p>
</div>

<script>
// Create floating particles
const particlesContainer = document.getElementById('particles');
for (let i = 0; i < 20; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.animationDelay = Math.random() * 15 + 's';
    particle.style.animationDuration = (10 + Math.random() * 10) + 's';
    particlesContainer.appendChild(particle);
}

// Rotating status messages
const messages = [
    "Analyzing your business data...",
    "Researching market trends...",
    "Calculating financial projections...",
    "Developing strategic recommendations...",
    "Crafting your unique business plan...",
    "Finalizing your business model..."
];

let messageIndex = 0;
const statusElement = document.getElementById('statusMessage');

setInterval(() => {
    messageIndex = (messageIndex + 1) % messages.length;
    statusElement.style.opacity = '0';
    setTimeout(() => {
        statusElement.textContent = messages[messageIndex];
        statusElement.style.opacity = '1';
    }, 300);
}, 3000);

// Fetch the result
fetch('/generate-result')
    .then(response => response.text())
    .then(html => {
        document.open();
        document.write(html);
        document.close();
    })
    .catch(error => {
        document.body.innerHTML = `
            <div style="text-align:center;color:white;padding:50px;">
                <h2>Something went wrong</h2>
                <p>Please <a href="/" style="color:#FFFADA;">try again</a></p>
            </div>
        `;
    });
</script>
</body>
</html>
"""

@app.route("/loading")
def loading():
    return render_template_string(LOADING_PAGE)

# =========================
# RESULT PAGE (UPGRADED)
# =========================

@app.route("/result")
def result():
    return render_template_string(LOADING_PAGE)

@app.route("/generate-result")
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
        <h2 style=\"color:red;text-align:center;\">
            API quota reached.<br>
            Please wait a minute and refresh this page.
        </h2>
        """

    html_output = markdown(
        r.text,
        extensions=["fenced_code", "tables", "toc", "attr_list"]
    )

    # === LOGO GENERATION ===
    business_name = business_snapshot.get("Business Name", "Untitled")
    logo_prompt = f"Generate a simple, modern, professional logo for a business named '{business_name}'. The logo should be visually appealing and suitable for a business plan. Return the image as a PNG."
    logo_filename = None
    logo_url = None
    try:
        # Use a Gemini model that supports image generation. Adjust model name if needed.
        logo_response = client.models.generate_content(
            model="gemini-2.5-pro-vision",  # Replace with the correct model for image generation if needed
            contents=logo_prompt,
            generation_config={"response_mime_type": "image/png"}
        )
        # The SDK may return image bytes as .binary or .image_data; adjust as needed
        image_bytes = getattr(logo_response, "binary", None) or getattr(logo_response, "image_data", None)
        if image_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logo_filename = f"logo_{timestamp}_{business_name.replace(' ', '_')}.png"
            logo_path = os.path.join(LOGO_DIR, logo_filename)
            with open(logo_path, "wb") as f:
                f.write(image_bytes)
            logo_url = f"/static/generated_logos/{logo_filename}"
            business_snapshot["Logo Image"] = logo_url
    except Exception as e:
        # If image generation fails, skip logo
        logo_url = None

    # Save the document
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    document = {
        "id": timestamp,
        "title": business_name,
        "created_at": datetime.now().isoformat(),
        "snapshot": business_snapshot,
        "content_markdown": r.text,
        "content_html": html_output,
        "logo_url": logo_url
    }

    # Save to JSON file
    filename = f"{timestamp}_{business_name.replace(' ', '_')}.json"
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(document, f, indent=2)

    # Render result page with logo if available
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
.logo-img {{
    display:block;
    margin:0 auto 24px auto;
    max-width:220px;
    max-height:220px;
    border-radius:16px;
    box-shadow:0 2px 12px rgba(0,0,0,.12);
}}
</style>
</head>
<body>
<div class=\"card\">
{f'<img src="{logo_url}" alt="Business Logo" class="logo-img">' if logo_url else ''}
<div class=\"markdown-output\">{html_output}</div>
<br>
<a href=\"/\">← Start Over</a>
</div>
</body>
</html>
"""

# --- API: Documents list & delete (used by client-side library)
@app.route('/api/documents')
def api_documents():
    docs = []
    if os.path.exists(DOCUMENTS_DIR):
        for filename in sorted(os.listdir(DOCUMENTS_DIR), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(DOCUMENTS_DIR, filename)) as f:
                    docs.append(json.load(f))
    return jsonify(docs)

@app.route('/api/documents/<doc_id>', methods=['DELETE'])
def api_delete_document(doc_id):
    # doc_id is the timestamp prefix we use when saving files
    found = False
    if os.path.exists(DOCUMENTS_DIR):
        for filename in os.listdir(DOCUMENTS_DIR):
            if filename.startswith(doc_id):
                os.remove(os.path.join(DOCUMENTS_DIR, filename))
                found = True
    if found:
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 404

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)
