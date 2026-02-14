import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, render_template_string
from google import genai
from google.genai import types
from markdown import markdown
import json
import re
from google.genai.errors import ClientError

# =========================================================
# PR #3: Load API key from .env via dotenv
# =========================================================
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
except ImportError:
    pass  # python-dotenv not installed; fall back to env / hardcoded key

app = Flask(__name__)

# =========================================================
# GEMINI API KEY (from .env or fallback)
# =========================================================
API_KEY = os.environ.get("OPENAI_API_KEY", "AIzaSyAPi78_IjFZunJLtq_-oYTnixB26RBX2U8")
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

# =========================================================
# PR #2: Navigation tabs used across all pages
# =========================================================
TABS = [
    ("Home", "/"),
    ("Builder", "/builder"),
    ("Library", "/library"),
]


# =========================
# HOME PAGE  (PR #2 — templates/index.html + navbar)
# =========================
@app.route("/")
def index():
    return render_template("index.html", tabs=TABS, active_tab="Home")


# =========================
# BUILDER PAGE  (PR #2 — chat + snapshot split-pane)
# =========================
@app.route("/builder")
def builder():
    return render_template("builder.html", tabs=TABS, active_tab="Builder")


# =========================
# LIBRARY PAGE  (PR #2 — saved documents)
# =========================
@app.route("/library")
def library():
    documents = []
    if os.path.exists(DOCUMENTS_DIR):
        for filename in sorted(os.listdir(DOCUMENTS_DIR), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(DOCUMENTS_DIR, filename)
                with open(filepath, 'r') as f:
                    doc = json.load(f)
                    documents.append(doc)
    return render_template("library.html", tabs=TABS, active_tab="Library", documents=documents)


# =========================
# DASHBOARD PAGE  (PR #2 — example / optional)
# =========================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", tabs=TABS, active_tab="Dashboard")


# =========================
# CHAT API ENDPOINT
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
                "reply": "API quota reached. Please wait about 1 minute and try again.",
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
# LOADING PAGE (shown while /generate-result runs)
# =========================
LOADING_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Generating Your Business Model...</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Arial',sans-serif;background:linear-gradient(135deg,#00264D 0%,#00498D 50%,#144C8C 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;overflow:hidden}
.loader-container{text-align:center;color:#fff}
.loader-title{font-size:28px;margin-bottom:40px;animation:fadeInUp .8s ease-out}
.loader-subtitle{font-size:16px;opacity:.8;margin-bottom:50px;animation:fadeInUp .8s ease-out .2s both}
.spinner{position:relative;width:100px;height:100px;margin:0 auto 40px}
.spinner-circle{position:absolute;width:100%;height:100%;border:4px solid transparent;border-radius:50%;animation:spin 1.5s linear infinite}
.spinner-circle:nth-child(1){border-top-color:#FFFADA}
.spinner-circle:nth-child(2){width:80%;height:80%;top:10%;left:10%;border-right-color:#D3CEBE;animation-delay:.15s;animation-direction:reverse}
.spinner-circle:nth-child(3){width:60%;height:60%;top:20%;left:20%;border-bottom-color:#fff;animation-delay:.3s}
@keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}
.progress-dots{display:flex;justify-content:center;gap:12px;margin-bottom:30px}
.dot{width:12px;height:12px;background:#FFFADA;border-radius:50%;animation:pulse 1.4s ease-in-out infinite}
.dot:nth-child(1){animation-delay:0s}.dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}.dot:nth-child(4){animation-delay:.6s}
@keyframes pulse{0%,100%{transform:scale(1);opacity:.4}50%{transform:scale(1.3);opacity:1}}
.status-message{font-size:14px;opacity:.9;animation:statusFade 3s ease-in-out infinite}
@keyframes statusFade{0%,100%{opacity:.5}50%{opacity:1}}
@keyframes fadeInUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.particles{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:hidden;z-index:-1}
.particle{position:absolute;width:6px;height:6px;background:rgba(255,250,218,.3);border-radius:50%;animation:float 15s infinite}
@keyframes float{0%,100%{transform:translateY(100vh) rotate(0);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateY(-100vh) rotate(720deg);opacity:0}}
</style>
</head>
<body>
<div class="particles" id="particles"></div>
<div class="loader-container">
  <h1 class="loader-title">Building Your Business Model</h1>
  <p class="loader-subtitle">Our AI is crafting a personalized plan just for you</p>
  <div class="spinner"><div class="spinner-circle"></div><div class="spinner-circle"></div><div class="spinner-circle"></div></div>
  <div class="progress-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
  <p class="status-message" id="statusMessage">Analyzing your business data...</p>
</div>
<script>
var pc=document.getElementById('particles');
for(var i=0;i<20;i++){var p=document.createElement('div');p.className='particle';p.style.left=Math.random()*100+'%';p.style.animationDelay=Math.random()*15+'s';p.style.animationDuration=(10+Math.random()*10)+'s';pc.appendChild(p)}
var msgs=["Analyzing your business data...","Researching market trends...","Calculating financial projections...","Developing strategic recommendations...","Crafting your unique business plan...","Finalizing your business model..."];
var mi=0;var se=document.getElementById('statusMessage');
setInterval(function(){mi=(mi+1)%msgs.length;se.style.opacity='0';setTimeout(function(){se.textContent=msgs[mi];se.style.opacity='1'},300)},3000);
fetch('/generate-result').then(function(r){return r.text()}).then(function(h){document.open();document.write(h);document.close()}).catch(function(){document.body.innerHTML='<div style="text-align:center;color:white;padding:50px;"><h2>Something went wrong</h2><p>Please <a href="/" style="color:#FFFADA;">try again</a></p></div>'});
</script>
</body>
</html>
"""


@app.route("/loading")
def loading():
    return render_template_string(LOADING_PAGE)


@app.route("/result")
def result():
    return render_template_string(LOADING_PAGE)


# =========================
# GENERATE-RESULT  (called by the loading page via fetch)
# =========================
@app.route("/generate-result")
def generate_result():
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

    # =========================================================
    # PR #1: LOGO GENERATION (fixed to use correct models & SDK API)
    # =========================================================
    business_name = business_snapshot.get("Business Name", "Untitled")
    logo_prompt = (
        f"Generate a simple, modern, professional logo for a business "
        f"named '{business_name}'. The logo should be clean, minimalist, "
        f"and suitable for a business plan."
    )
    logo_filename = None
    logo_url = None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Try free Gemini image-capable models
    IMAGE_MODELS = [
        "gemini-2.0-flash-exp-image-generation",
        "gemini-2.5-flash-image",
        "gemini-3-pro-image-preview",
    ]
    for img_model in IMAGE_MODELS:
        if logo_url:
            break
        try:
            logo_response = client.models.generate_content(
                model=img_model,
                contents=logo_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                )
            )
            if logo_response.candidates:
                for part in logo_response.candidates[0].content.parts:
                    if (part.inline_data
                            and part.inline_data.mime_type
                            and part.inline_data.mime_type.startswith("image/")):
                        logo_filename = f"logo_{timestamp}_{business_name.replace(' ', '_')}.png"
                        logo_path = os.path.join(LOGO_DIR, logo_filename)
                        with open(logo_path, "wb") as f:
                            f.write(part.inline_data.data)
                        logo_url = f"/static/generated_logos/{logo_filename}"
                        business_snapshot["Logo Image"] = logo_url
                        print(f"Logo generated with {img_model}")
                        break
        except Exception as e:
            print(f"{img_model} failed: {e}")

    # Fallback: try Imagen 4 (requires billing)
    if not logo_url:
        for img_model in ["imagen-4.0-fast-generate-001", "imagen-4.0-generate-001"]:
            if logo_url:
                break
            try:
                logo_response = client.models.generate_images(
                    model=img_model,
                    prompt=logo_prompt,
                    config=types.GenerateImagesConfig(number_of_images=1)
                )
                if logo_response.generated_images:
                    image = logo_response.generated_images[0].image
                    if image and image.image_bytes:
                        logo_filename = f"logo_{timestamp}_{business_name.replace(' ', '_')}.png"
                        logo_path = os.path.join(LOGO_DIR, logo_filename)
                        with open(logo_path, "wb") as f:
                            f.write(image.image_bytes)
                        logo_url = f"/static/generated_logos/{logo_filename}"
                        business_snapshot["Logo Image"] = logo_url
                        print(f"Logo generated with {img_model}")
            except Exception as e:
                print(f"{img_model} failed: {e}")

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

    filename = f"{timestamp}_{business_name.replace(' ', '_')}.json"
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(document, f, indent=2)

    # Build the logo HTML snippet
    logo_html = ""
    if logo_url:
        logo_html = f'<img src="{logo_url}" alt="Business Logo" class="logo-img">'

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
<div class="card">
{logo_html}
<div class="markdown-output">{html_output}</div>
<br>
<a href="/">&#8592; Start Over</a>
</div>
</body>
</html>
"""


# =========================
# API: Documents list & delete (used by library/homepage JS)
# =========================
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
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
 