import html
import json
import uuid
from typing import Any, Dict, List


def render_quiz(title: str, questions: List[Dict[str, Any]], user_answers: Dict[int, str] = None) -> None:
    """
    Renders a true interactive Udemy-style quiz inside Jupyter / VS Code:
      1. Displays radio-button choices with ZERO spoilers (explanations & implications hidden).
      2. Developer selects A, B, or C for each question and clicks 'Submit Quiz'.
      3. Client-side JS grades all 3 answers, calculates percentage score, highlights
         correct/incorrect choices, and reveals both Explanation and Production Implication.
    """
    quiz_id = f"quiz_{uuid.uuid4().hex[:10]}"
    safe_title = html.escape(title)

    # Encode grading key & rich feedback safely in a JSON script block (not visible until submit)
    answer_key = {}
    cards_html = []

    for idx, q in enumerate(questions, start=1):
        q_text = html.escape(q["question"])
        options = q["options"]
        correct_key = q["answer"].strip().upper()
        explanation = q.get("explanation", "")
        implication = q.get(
            "implication",
            "Applying this pattern prevents silent accuracy regressions and unbounded latency in production.",
        )

        answer_key[str(idx)] = {
            "correct": correct_key,
            "explanation": explanation,
            "implication": implication,
        }

        opts_html = []
        for opt_k, opt_v in options.items():
            opt_k_clean = html.escape(opt_k.strip().upper())
            opt_v_clean = html.escape(opt_v)
            input_id = f"{quiz_id}_q{idx}_{opt_k_clean}"
            opts_html.append(
                f"<label id='{input_id}_lbl' for='{input_id}' "
                f"style='display:flex; align-items:flex-start; gap:10px; padding:10px 12px; margin:6px 0; "
                f"border-radius:8px; border:1px solid #cbd5e1; background:#f8fafc; cursor:pointer; color:#0f172a; transition:all 0.15s;'>"
                f"<input type='radio' id='{input_id}' name='{quiz_id}_q{idx}' value='{opt_k_clean}' "
                f"style='margin-top:3px; accent-color:#4f46e5; cursor:pointer;' />"
                f"<span><strong>{opt_k_clean}.</strong> {opt_v_clean}</span>"
                f"</label>"
            )

        cards_html.append(
            f"<div id='{quiz_id}_card_{idx}' style='border:1px solid #cbd5e1; border-radius:10px; padding:16px; margin-bottom:14px; background:#ffffff;'>"
            f"<div style='font-weight:700; font-size:14px; color:#0f172a; margin-bottom:10px;'>Question {idx} of {len(questions)}: {q_text}</div>"
            f"{''.join(opts_html)}"
            f"<div id='{quiz_id}_fb_{idx}' style='display:none; margin-top:12px; padding:12px 14px; border-radius:8px; font-size:13px; line-height:1.5;'></div>"
            f"</div>"
        )

    key_json = json.dumps(answer_key).replace("</", "<\/")

    html_block = f"""
<div id="{quiz_id}_container" style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; border:1px solid #94a3b8; border-radius:12px; padding:18px; background:#f1f5f9; color:#0f172a; max-width:920px;">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:14px; border-bottom:1px solid #cbd5e1; padding-bottom:10px;">
    <div>
      <div style="font-size:16px; font-weight:800; color:#1e293b;">{safe_title}</div>
      <div style="font-size:12px; color:#475569;">Select one option for all {len(questions)} questions, then click <strong>Submit Quiz</strong> to reveal grading, explanations &amp; production implications.</div>
    </div>
    <div id="{quiz_id}_banner" style="font-size:13px; font-weight:700; padding:6px 12px; border-radius:999px; background:#e0e7ff; color:#3730a3;">
      {len(questions)} Questions &bull; Ready
    </div>
  </div>

  {''.join(cards_html)}

  <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
    <button type="button" id="{quiz_id}_submit"
      style="background:#4f46e5; color:#ffffff; border:none; border-radius:8px; padding:10px 20px; font-size:14px; font-weight:700; cursor:pointer; box-shadow:0 1px 2px rgba(0,0,0,0.1);">
      Submit Quiz
    </button>
    <button type="button" id="{quiz_id}_reset"
      style="background:#ffffff; color:#334155; border:1px solid #cbd5e1; border-radius:8px; padding:10px 16px; font-size:13px; font-weight:600; cursor:pointer;">
      Retake Quiz
    </button>
    <span id="{quiz_id}_warn" style="font-size:13px; font-weight:600; color:#b45309; display:none;"></span>
  </div>

  <script type="application/json" id="{quiz_id}_key">{key_json}</script>
  <script>
  (function() {{
    var root = document.getElementById("{quiz_id}_container");
    if (!root) return;
    var keyData = JSON.parse(document.getElementById("{quiz_id}_key").textContent);
    var total = Object.keys(keyData).length;
    var submitBtn = document.getElementById("{quiz_id}_submit");
    var resetBtn = document.getElementById("{quiz_id}_reset");
    var banner = document.getElementById("{quiz_id}_banner");
    var warn = document.getElementById("{quiz_id}_warn");

    function escapeHtml(str) {{
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    submitBtn.addEventListener("click", function() {{
      var missing = [];
      for (var i = 1; i <= total; i++) {{
        var selected = root.querySelector("input[name='{quiz_id}_q" + i + "']:checked");
        if (!selected) missing.push("Q" + i);
      }}
      if (missing.length > 0) {{
        warn.textContent = "Please answer " + missing.join(", ") + " before submitting.";
        warn.style.display = "inline";
        return;
      }}
      warn.style.display = "none";

      var correctCount = 0;
      for (var qIdx = 1; qIdx <= total; qIdx++) {{
        var item = keyData[String(qIdx)];
        var radios = root.querySelectorAll("input[name='{quiz_id}_q" + qIdx + "']");
        var pickedVal = "";
        radios.forEach(function(r) {{
          r.disabled = true;
          var lbl = document.getElementById(r.id + "_lbl");
          lbl.style.cursor = "default";
          if (r.checked) pickedVal = r.value;
          if (r.value === item.correct) {{
            lbl.style.background = "#dcfce7";
            lbl.style.borderColor = "#16a34a";
            lbl.style.fontWeight = "600";
          }} else if (r.checked && r.value !== item.correct) {{
            lbl.style.background = "#fee2e2";
            lbl.style.borderColor = "#dc2626";
          }}
        }});

        var isRight = (pickedVal === item.correct);
        if (isRight) correctCount++;

        var fb = document.getElementById("{quiz_id}_fb_" + qIdx);
        fb.style.display = "block";
        if (isRight) {{
          fb.style.background = "#f0fdf4";
          fb.style.border = "1px solid #86efac";
          fb.style.color = "#14532d";
          fb.innerHTML =
            "<div><strong>&#10004; Correct (" + item.correct + ")</strong></div>" +
            "<div style='margin-top:4px;'><strong>Explanation:</strong> " + escapeHtml(item.explanation) + "</div>" +
            "<div style='margin-top:4px;'><strong>Production Implication:</strong> " + escapeHtml(item.implication) + "</div>";
        }} else {{
          fb.style.background = "#fef2f2";
          fb.style.border = "1px solid #fca5a5";
          fb.style.color = "#7f1d1d";
          fb.innerHTML =
            "<div><strong>&#10008; Incorrect (You chose " + pickedVal + " &bull; Correct answer: " + item.correct + ")</strong></div>" +
            "<div style='margin-top:4px;'><strong>Explanation:</strong> " + escapeHtml(item.explanation) + "</div>" +
            "<div style='margin-top:4px;'><strong>Production Implication:</strong> " + escapeHtml(item.implication) + "</div>";
        }}
      }}

      var pct = Math.round((correctCount / total) * 100);
      banner.textContent = "Score: " + correctCount + "/" + total + " (" + pct + "%)";
      banner.style.background = (correctCount === total) ? "#dcfce7" : "#fef3c7";
      banner.style.color = (correctCount === total) ? "#166534" : "#92400e";
      submitBtn.disabled = true;
      submitBtn.style.opacity = "0.6";
      submitBtn.style.cursor = "default";
    }});

    resetBtn.addEventListener("click", function() {{
      for (var qIdx = 1; qIdx <= total; qIdx++) {{
        var radios = root.querySelectorAll("input[name='{quiz_id}_q" + qIdx + "']");
        radios.forEach(function(r) {{
          r.disabled = false;
          r.checked = false;
          var lbl = document.getElementById(r.id + "_lbl");
          lbl.style.background = "#f8fafc";
          lbl.style.borderColor = "#cbd5e1";
          lbl.style.fontWeight = "400";
          lbl.style.cursor = "pointer";
        }});
        var fb = document.getElementById("{quiz_id}_fb_" + qIdx);
        fb.style.display = "none";
        fb.innerHTML = "";
      }}
      warn.style.display = "none";
      banner.textContent = total + " Questions \u2022 Ready";
      banner.style.background = "#e0e7ff";
      banner.style.color = "#3730a3";
      submitBtn.disabled = false;
      submitBtn.style.opacity = "1";
      submitBtn.style.cursor = "pointer";
    }});
  }})();
  </script>
</div>
"""

    try:
        from IPython.display import HTML, display
        display(HTML(html_block))
    except ImportError:
        print(f"{title} — {len(questions)} questions ready.")
