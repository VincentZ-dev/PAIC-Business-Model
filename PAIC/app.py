from flask import Flask, request, jsonify, render_template, send_from_directory
from google import genai
from markdown import markdown
import json
import re
import os
from datetime import datetime
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
# MAIN PAGE
# =========================
@app.route("/")
def index():
    tabs = [
        ("Home", "/"),
        ("Library", "/library")
    ]
    return render_template("index.html", tabs=tabs, active_tab="Home")

# =========================
# ABOUT PAGE
# =========================
@app.route("/library")
def library():
    tabs = [
        ("Home", "/"),
        ("Library", "/library")
    ]
    
    # Load all saved documents
    documents = []
    if os.path.exists(DOCUMENTS_DIR):
        for filename in sorted(os.listdir(DOCUMENTS_DIR), reverse=True):
            if filename.endswith('.json'):
                filepath = os.path.join(DOCUMENTS_DIR, filename)
                with open(filepath, 'r') as f:
                    doc = json.load(f)
                    documents.append(doc)
    
    return render_template("library.html", tabs=tabs, active_tab="Library", documents=documents)

# =========================
# DASHBOARD PAGE (EXAMPLE)
# =========================
# Uncomment this to add a Dashboard tab:
# @app.route("/dashboard")
# def dashboard():
#     tabs = [
#         ("Home", "/"),
#         ("Dashboard", "/dashboard"),
#         ("About", "/about")
#     ]
#     return render_template("dashboard.html", tabs=tabs, active_tab="Dashboard")
#
# Then update all other routes to include the Dashboard tab in their tabs list!

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
# RESULT PAGE
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

@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)