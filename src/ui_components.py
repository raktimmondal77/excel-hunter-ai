import json

def get_match_gauge_html(score: int, recommendation: str, reasoning: str) -> str:
    """
    Renders an animated glowing circular SVG match gauge with recommendation badge.
    """
    if score >= 70:
        stroke_color = "#10B981"
        glow_color = "rgba(16, 185, 129, 0.3)"
        badge_bg = "#ECFDF5"
        badge_border = "#A7F3D0"
        badge_text = "#065F46"
        icon = "✅"
    elif score >= 50:
        stroke_color = "#F59E0B"
        glow_color = "rgba(245, 158, 11, 0.3)"
        badge_bg = "#FFFBEB"
        badge_border = "#FDE68A"
        badge_text = "#92400E"
        icon = "💡"
    else:
        stroke_color = "#EF4444"
        glow_color = "rgba(239, 68, 68, 0.3)"
        badge_bg = "#FEF2F2"
        badge_border = "#FECACA"
        badge_text = "#991B1B"
        icon = "⚠️"

    circumference = 2 * 3.14159 * 52
    offset = circumference - (score / 100.0) * circumference

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
                background: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .gauge-card {{
                background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                padding: 22px 28px;
                box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
                display: flex;
                align-items: center;
                gap: 28px;
                max-width: 720px;
                width: 100%;
                box-sizing: border-box;
            }}
            .svg-wrap {{
                position: relative;
                width: 130px;
                height: 130px;
                flex-shrink: 0;
            }}
            svg {{
                transform: rotate(-90deg);
                width: 130px;
                height: 130px;
            }}
            .circle-bg {{
                fill: none;
                stroke: #E2E8F0;
                stroke-width: 10;
            }}
            .circle-progress {{
                fill: none;
                stroke: {stroke_color};
                stroke-width: 10;
                stroke-linecap: round;
                stroke-dasharray: {circumference};
                stroke-dashoffset: {offset};
                transition: stroke-dashoffset 1s ease-in-out;
                filter: drop-shadow(0 0 6px {glow_color});
            }}
            .gauge-number {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 1.85rem;
                color: #0F172A;
                line-height: 1;
            }}
            .gauge-number span {{
                font-size: 0.75rem;
                font-weight: 700;
                color: #64748B;
                margin-top: 2px;
            }}
            .gauge-info {{
                flex-grow: 1;
            }}
            .rec-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 14px;
                border-radius: 9999px;
                font-size: 0.85rem;
                font-weight: 700;
                background: {badge_bg};
                border: 1px solid {badge_border};
                color: {badge_text};
                margin-bottom: 8px;
            }}
            .reason-text {{
                font-size: 0.9rem;
                color: #475569;
                line-height: 1.45;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="gauge-card">
            <div class="svg-wrap">
                <svg>
                    <circle class="circle-bg" cx="65" cy="65" r="52"></circle>
                    <circle class="circle-progress" cx="65" cy="65" r="52"></circle>
                </svg>
                <div class="gauge-number">
                    {score}
                    <span>SCORE</span>
                </div>
            </div>
            <div class="gauge-info">
                <div class="rec-badge">{icon} {recommendation.upper()}</div>
                <p class="reason-text">{reasoning}</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_copy_box_html(text_to_copy: str, title: str = "Ready-Made Proposal") -> str:
    """
    Renders an interactive proposal copy box with live JavaScript copy-to-clipboard
    and a floating animated toast notification.
    """
    safe_text_json = json.dumps(text_to_copy)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Plus Jakarta Sans', sans-serif;
                background: transparent;
            }}
            .copy-container {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px 20px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                position: relative;
            }}
            .header-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }}
            .title {{
                font-size: 0.95rem;
                font-weight: 700;
                color: #0F172A;
            }}
            .copy-btn {{
                background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 0.82rem;
                font-weight: 700;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s ease;
                box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
            }}
            .copy-btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
            }}
            .copy-btn:active {{
                transform: translateY(1px);
            }}
            .toast {{
                position: fixed;
                top: 12px;
                right: 16px;
                background: #065F46;
                color: #FFFFFF;
                padding: 10px 18px;
                border-radius: 8px;
                font-size: 0.85rem;
                font-weight: 700;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                opacity: 0;
                transform: translateY(-10px);
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                pointer-events: none;
                z-index: 9999;
            }}
            .toast.show {{
                opacity: 1;
                transform: translateY(0);
            }}
            .char-pill {{
                font-size: 0.75rem;
                color: #64748B;
                background: #F1F5F9;
                padding: 2px 8px;
                border-radius: 4px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="copy-container">
            <div class="header-bar">
                <span class="title">📋 {title}</span>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="char-pill" id="word-count">{len(text_to_copy.split())} words</span>
                    <button class="copy-btn" id="btn-copy" onclick="doCopy()">
                        <span id="btn-icon">📋</span>
                        <span id="btn-text">Copy Proposal</span>
                    </button>
                </div>
            </div>
            <div class="toast" id="toast-msg">✨ Copied to clipboard! Ready to paste to client.</div>
        </div>

        <script>
            const textContent = {safe_text_json};
            function doCopy() {{
                navigator.clipboard.writeText(textContent).then(() => {{
                    const btn = document.getElementById("btn-copy");
                    const icon = document.getElementById("btn-icon");
                    const text = document.getElementById("btn-text");
                    const toast = document.getElementById("toast-msg");

                    btn.style.background = "#059669";
                    icon.innerText = "✓";
                    text.innerText = "Copied!";
                    toast.classList.add("show");

                    setTimeout(() => {{
                        btn.style.background = "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)";
                        icon.innerText = "📋";
                        text.innerText = "Copy Proposal";
                        toast.classList.remove("show");
                    }}, 2500);
                }}).catch(err => {{
                    alert("Copy failed, please select and copy manually.");
                }});
            }}
        </script>
    </body>
    </html>
    """

def get_income_simulator_html(current_net: float = 0.0, target_min: float = 10000.0, target_max: float = 20000.0) -> str:
    """
    Renders an interactive real-time JavaScript calculator for the user's monthly income goals.
    Drag sliders for 'Projects per Month' and 'Average Bid' to see instantaneous take-home estimates.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Plus Jakarta Sans', sans-serif;
                background: transparent;
            }}
            .sim-box {{
                background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
                border-radius: 16px;
                padding: 24px 28px;
                color: #FFFFFF;
                box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .sim-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 18px;
            }}
            .sim-title {{
                font-size: 1.15rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                color: #F8FAFC;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .slider-group label {{
                display: flex;
                justify-content: space-between;
                font-size: 0.82rem;
                color: #94A3B8;
                font-weight: 600;
                margin-bottom: 6px;
            }}
            .slider-group label b {{
                color: #60A5FA;
                font-family: 'JetBrains Mono', monospace;
            }}
            input[type="range"] {{
                width: 100%;
                accent-color: #3B82F6;
                cursor: pointer;
            }}
            .results-panel {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px 20px;
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                text-align: center;
            }}
            .res-label {{
                font-size: 0.72rem;
                color: #94A3B8;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-weight: 700;
                margin-bottom: 4px;
            }}
            .res-val {{
                font-size: 1.35rem;
                font-weight: 800;
                font-family: 'JetBrains Mono', monospace;
            }}
            .progress-track {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 9999px;
                height: 8px;
                overflow: hidden;
                margin-top: 14px;
            }}
            .progress-fill {{
                background: linear-gradient(90deg, #10B981, #3B82F6);
                height: 100%;
                width: 0%;
                transition: width 0.3s ease;
            }}
        </style>
    </head>
    <body>
        <div class="sim-box">
            <div class="sim-header">
                <div class="sim-title">⚡ Interactive Monthly Income Simulator</div>
                <span style="font-size: 0.78rem; background: rgba(59, 130, 246, 0.2); color: #93C5FD; padding: 3px 10px; border-radius: 9999px; font-weight: 700;">Live JS Modeling</span>
            </div>

            <div class="grid">
                <div class="slider-group">
                    <label>Projects Won Per Month: <b id="val-projects">5 projects</b></label>
                    <input type="range" id="input-projects" min="1" max="15" value="5" oninput="updateSim()">
                </div>
                <div class="slider-group">
                    <label>Average Project Price: <b id="val-price">₹3,000</b></label>
                    <input type="range" id="input-price" min="1000" max="15000" step="500" value="3000" oninput="updateSim()">
                </div>
            </div>

            <div class="results-panel">
                <div>
                    <div class="res-label">Gross Revenue</div>
                    <div class="res-val" style="color: #F8FAFC;" id="out-gross">₹15,000</div>
                </div>
                <div>
                    <div class="res-label">Platform Fee (10%)</div>
                    <div class="res-val" style="color: #F59E0B;" id="out-fee">-₹1,500</div>
                </div>
                <div>
                    <div class="res-label">Net Take-Home</div>
                    <div class="res-val" style="color: #34D399;" id="out-net">₹13,500</div>
                </div>
            </div>

            <div class="progress-track">
                <div class="progress-fill" id="sim-progress-bar"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #94A3B8; margin-top: 6px;">
                <span>₹0</span>
                <span>₹10,000 Min Target</span>
                <span>₹20,000 Top Target</span>
            </div>
        </div>

        <script>
            function updateSim() {{
                const projects = parseInt(document.getElementById("input-projects").value);
                const price = parseInt(document.getElementById("input-price").value);

                document.getElementById("val-projects").innerText = projects + " projects";
                document.getElementById("val-price").innerText = "₹" + price.toLocaleString("en-IN");

                const gross = projects * price;
                const fee = gross * 0.10;
                const net = gross - fee;

                document.getElementById("out-gross").innerText = "₹" + gross.toLocaleString("en-IN");
                document.getElementById("out-fee").innerText = "-₹" + fee.toLocaleString("en-IN");
                document.getElementById("out-net").innerText = "₹" + net.toLocaleString("en-IN");

                const maxGoal = {target_max};
                const pct = Math.min(100, Math.round((net / maxGoal) * 100));
                document.getElementById("sim-progress-bar").style.width = pct + "%";
            }}
            updateSim();
        </script>
    </body>
    </html>
    """
