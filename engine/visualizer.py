import html
import json
from typing import Any, Dict, List, Optional

class StoryVisualizer:
    """
    Renders rich, story-driven HTML/SVG X-Ray Pipeline Storyboards directly inside Jupyter cells
    so newbie engineers can visually see each building block transform data step-by-step.
    """
    @staticmethod
    def render_story(
        title: str,
        stages: List[Dict[str, Any]],
        phoenix_url: Optional[str] = None
    ):
        from IPython.display import display, HTML

        stage_cards = []
        for idx, st in enumerate(stages, start=1):
            st_name = html.escape(str(st.get("name", f"Stage {idx}")))
            st_badge = html.escape(str(st.get("badge", "STEP")))
            st_latency = st.get("latency_ms", None)
            lat_html = f"<span style='background:#1e293b;color:#38bdf8;padding:2px 8px;border-radius:10px;font-size:11px;margin-left:8px;'>{st_latency} ms</span>" if st_latency is not None else ""
            summary = html.escape(str(st.get("summary", "")))
            payload = st.get("payload", "")
            if isinstance(payload, (dict, list)):
                payload_str = html.escape(json.dumps(payload, indent=2))
            else:
                payload_str = html.escape(str(payload))

            bars_html = ""
            if "scores" in st and isinstance(st["scores"], list):
                rows = []
                for item in st["scores"]:
                    lbl = html.escape(str(item.get("label", "")))
                    sc = float(item.get("score", 0.0))
                    pct = max(2, min(100, int(sc * 100)))
                    color = "#10b981" if sc >= 0.5 else ("#f59e0b" if sc >= 0.25 else "#64748b")
                    rows.append(
                        f"<div style='margin:4px 0;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:12px;color:#cbd5e1;'><span>{lbl}</span><span><b>{sc:.3f}</b></span></div>"
                        f"<div style='background:#1e293b;border-radius:4px;height:8px;overflow:hidden;'>"
                        f"<div style='width:{pct}%;background:{color};height:100%;'></div></div></div>"
                    )
                bars_html = f"<div style='margin:8px 0;padding:8px;background:#0f172a;border-radius:6px;'>{''.join(rows)}</div>"

            arrow = "<div style='text-align:center;color:#38bdf8;font-size:18px;font-weight:bold;margin:4px 0;'>&#8595;</div>" if idx < len(stages) else ""

            card = f"""
            <div style="background:#1e293b;border-left:4px solid #38bdf8;border-radius:8px;padding:12px 16px;margin-bottom:4px;box-shadow:0 2px 6px rgba(0,0,0,0.25);">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <span style="background:#0284c7;color:#fff;font-size:10px;font-weight:bold;padding:2px 7px;border-radius:4px;text-transform:uppercase;margin-right:8px;">{st_badge}</span>
                        <strong style="color:#f8fafc;font-size:14px;">{idx}. {st_name}</strong>
                        {lat_html}
                    </div>
                </div>
                <p style="color:#94a3b8;font-size:12.5px;margin:6px 0 8px 0;">{summary}</p>
                {bars_html}
                <pre style="background:#0f172a;color:#e2e8f0;padding:10px;border-radius:6px;font-size:11.5px;overflow-x:auto;margin:0;white-space:pre-wrap;">{payload_str}</pre>
            </div>
            {arrow}
            """
            stage_cards.append(card)

        phoenix_banner = ""
        if phoenix_url:
            phoenix_banner = f"<div style='margin-top:8px;font-size:12px;color:#34d399;'>&#128269; Live OpenTelemetry Traces active at: <a href='{phoenix_url}' target='_blank' style='color:#38bdf8;'>{phoenix_url}</a></div>"

        full_html = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#f8fafc;padding:16px;border-radius:10px;border:1px solid #334155;margin:10px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:12px;">
                <h3 style="margin:0;color:#38bdf8;font-size:16px;">&#128300; X-Ray Pipeline Storyboard: {html.escape(title)}</h3>
                <span style="font-size:11px;color:#94a3b8;">Offline Local Runtime</span>
            </div>
            {''.join(stage_cards)}
            {phoenix_banner}
        </div>
        """
        display(HTML(full_html))
