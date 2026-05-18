"""Beautiful HTML email templates for PLAYBOOK alerts.

Each template is designed as a responsive, dark-themed email with:
- Severity-colored badges and borders
- Agent communication evidence cards
- Judge verdict highlights
- Clean typography and spacing
"""

from datetime import datetime
from typing import Any, Dict, Optional


def _severity_color(severity: str) -> str:
    """Return hex color for severity level."""
    s = (severity or "").lower()
    if s == "critical":
        return "#DC2626"
    if s == "high":
        return "#EA580C"
    if s == "medium":
        return "#CA8A04"
    return "#16A34A"


def _severity_bg(severity: str) -> str:
    """Return light background color for severity level."""
    s = (severity or "").lower()
    if s == "critical":
        return "#FEF2F2"
    if s == "high":
        return "#FFF7ED"
    if s == "medium":
        return "#FEFCE8"
    return "#F0FDF4"


def incident_alert_html(
    incident_id: str,
    incident_type: str,
    incident_type_name: str,
    severity: str,
    agent_id: Optional[str],
    swarm_id: Optional[str],
    reasoning: Optional[str],
    tool_call: Optional[str],
    judge_verdict: Optional[str],
    judge_rationale: Optional[str],
    timestamp: Optional[str] = None,
    dashboard_url: str = "https://playbooksoar.aiproofofconcept.in/incidents",
) -> str:
    """Render a stunning HTML incident alert email."""
    color = _severity_color(severity)
    bg = _severity_bg(severity)
    ts = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    agent_block = ""
    if agent_id:
        agent_block = f"""
        <tr>
          <td style="padding:4px 0; color:#6B7280; font-size:13px;">Agent</td>
          <td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right;">{agent_id}</td>
        </tr>
        """
    swarm_block = ""
    if swarm_id:
        swarm_block = f"""
        <tr>
          <td style="padding:4px 0; color:#6B7280; font-size:13px;">Swarm / Session</td>
          <td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right;">{swarm_id}</td>
        </tr>
        """

    reasoning_block = ""
    if reasoning:
        reasoning_block = f"""
        <div style="margin-top:20px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:18px;">
          <p style="margin:0 0 10px 0; font-size:11px; font-weight:700; color:#3B82F6; text-transform:uppercase; letter-spacing:0.5px;">🤖 Agent Reasoning</p>
          <p style="margin:0; font-size:14px; color:#1E293B; line-height:1.6; font-style:italic;">"{reasoning}"</p>
        </div>
        """

    tool_call_block = ""
    if tool_call:
        tool_call_block = f"""
        <div style="margin-top:16px; background:#FFF7ED; border:2px solid #FDBA74; border-radius:10px; padding:18px;">
          <p style="margin:0 0 10px 0; font-size:11px; font-weight:700; color:#EA580C; text-transform:uppercase; letter-spacing:0.5px;">⚡ Blocked Command / Tool Call</p>
          <pre style="margin:0; padding:12px; background:#FFF; border:1px solid #FED7AA; border-radius:6px; font-family:'SF Mono', Monaco, Consolas, monospace; font-size:12px; color:#7C2D12; overflow-x:auto;">{tool_call}</pre>
        </div>
        """

    judge_block = ""
    if judge_verdict:
        verdict_color = "#DC2626" if judge_verdict == "DENY" else "#16A34A" if judge_verdict == "ALLOW" else "#EA580C"
        verdict_bg = "#FEF2F2" if judge_verdict == "DENY" else "#F0FDF4" if judge_verdict == "ALLOW" else "#FFF7ED"
        judge_block = f"""
        <div style="margin-top:16px; background:{verdict_bg}; border:1px solid {verdict_color}40; border-radius:10px; padding:18px;">
          <p style="margin:0 0 10px 0; font-size:11px; font-weight:700; color:{verdict_color}; text-transform:uppercase; letter-spacing:0.5px;">⚖️ Judge Layer Verdict</p>
          <div style="display:inline-block; padding:6px 14px; background:{verdict_color}; color:#FFF; border-radius:20px; font-size:13px; font-weight:700; margin-bottom:10px;">{judge_verdict}</div>
          <p style="margin:0; font-size:14px; color:#374151; line-height:1.6;">{judge_rationale or "No rationale provided."}</p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PLAYBOOK Alert</title>
</head>
<body style="margin:0; padding:0; background:#F1F5F9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F1F5F9;">
  <tr>
    <td align="center" style="padding:40px 16px;">
      <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px; width:100%; background:#FFFFFF; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:#0F172A; padding:28px 32px; text-align:center;">
            <p style="margin:0; font-size:20px; font-weight:800; color:#FFFFFF; letter-spacing:1px;">PLAYBOOK</p>
            <p style="margin:6px 0 0 0; font-size:11px; color:#94A3B8; text-transform:uppercase; letter-spacing:2px;">AI Agent Security Platform</p>
          </td>
        </tr>
        <!-- Alert Banner -->
        <tr>
          <td style="background:{bg}; border-left:6px solid {color}; padding:24px 32px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
              <tr>
                <td>
                  <span style="display:inline-block; padding:4px 12px; background:{color}; color:#FFFFFF; border-radius:20px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{severity.upper()}</span>
                </td>
                <td style="text-align:right;">
                  <span style="font-size:12px; color:#6B7280; font-family:monospace;">{incident_id}</span>
                </td>
              </tr>
            </table>
            <h1 style="margin:14px 0 0 0; font-size:22px; font-weight:700; color:#111827;">{incident_type_name}</h1>
            <p style="margin:6px 0 0 0; font-size:13px; color:#6B7280; font-family:monospace;">{incident_type}</p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:28px 32px;">
            <p style="margin:0 0 20px 0; font-size:14px; color:#374151; line-height:1.6;">
              The PLAYBOOK Judge Layer has detected and blocked a suspicious agent action. Below is the complete evidence captured at the time of interception.
            </p>

            <!-- Incident Details Card -->
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:20px;">
              <p style="margin:0 0 14px 0; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">Incident Details</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td style="padding:4px 0; color:#6B7280; font-size:13px;">Incident ID</td>
                  <td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right; font-family:monospace;">{incident_id}</td>
                </tr>
                <tr>
                  <td style="padding:4px 0; color:#6B7280; font-size:13px;">Severity</td>
                  <td style="padding:4px 0; color:{color}; font-size:13px; font-weight:700; text-align:right;">{severity.upper()}</td>
                </tr>
                <tr>
                  <td style="padding:4px 0; color:#6B7280; font-size:13px;">Detected At</td>
                  <td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right;">{ts}</td>
                </tr>
                {agent_block}
                {swarm_block}
              </table>
            </div>

            {reasoning_block}
            {tool_call_block}
            {judge_block}

            <!-- CTA -->
            <div style="margin-top:28px; text-align:center;">
              <a href="{dashboard_url}/{incident_id}" style="display:inline-block; padding:14px 32px; background:#2563EB; color:#FFFFFF; text-decoration:none; border-radius:8px; font-size:14px; font-weight:600;">View Full Incident in Dashboard →</a>
            </div>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#F8FAFC; padding:20px 32px; text-align:center; border-top:1px solid #E2E8F0;">
            <p style="margin:0; font-size:12px; color:#94A3B8;">PLAYBOOK AI Agent Security • Automated Alert</p>
            <p style="margin:6px 0 0 0; font-size:11px; color:#CBD5E1;">{ts}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def judge_verdict_alert_html(
    incident_id: str,
    agent_id: Optional[str],
    verdict: str,
    rationale: str,
    severity: str,
    timestamp: Optional[str] = None,
    dashboard_url: str = "https://playbooksoar.aiproofofconcept.in/incidents",
) -> str:
    """Render a Judge Layer verdict alert email."""
    color = "#DC2626" if verdict == "DENY" else "#16A34A" if verdict == "ALLOW" else "#EA580C"
    bg = "#FEF2F2" if verdict == "DENY" else "#F0FDF4" if verdict == "ALLOW" else "#FFF7ED"
    ts = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Judge Verdict</title></head>
<body style="margin:0; padding:0; background:#F1F5F9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F1F5F9;">
  <tr><td align="center" style="padding:40px 16px;">
    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px; width:100%; background:#FFFFFF; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
      <tr><td style="background:#0F172A; padding:28px 32px; text-align:center;">
        <p style="margin:0; font-size:20px; font-weight:800; color:#FFFFFF; letter-spacing:1px;">PLAYBOOK</p>
        <p style="margin:6px 0 0 0; font-size:11px; color:#94A3B8; text-transform:uppercase; letter-spacing:2px;">Judge Layer Verdict</p>
      </td></tr>
      <tr><td style="background:{bg}; border-left:6px solid {color}; padding:24px 32px;">
        <div style="display:inline-block; padding:6px 14px; background:{color}; color:#FFF; border-radius:20px; font-size:13px; font-weight:700;">{verdict}</div>
        <h1 style="margin:14px 0 0 0; font-size:20px; font-weight:700; color:#111827;">Verdict: {verdict}</h1>
        <p style="margin:6px 0 0 0; font-size:13px; color:#6B7280; font-family:monospace;">{incident_id}</p>
      </td></tr>
      <tr><td style="padding:28px 32px;">
        <p style="margin:0 0 16px 0; font-size:14px; color:#374151; line-height:1.6;"><strong>Agent:</strong> {agent_id or "Unknown"}</p>
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:18px;">
          <p style="margin:0 0 10px 0; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px;">Rationale</p>
          <p style="margin:0; font-size:14px; color:#1E293B; line-height:1.6;">{rationale}</p>
        </div>
        <div style="margin-top:24px; text-align:center;">
          <a href="{dashboard_url}/{incident_id}" style="display:inline-block; padding:14px 32px; background:#2563EB; color:#FFFFFF; text-decoration:none; border-radius:8px; font-size:14px; font-weight:600;">View in Dashboard →</a>
        </div>
      </td></tr>
      <tr><td style="background:#F8FAFC; padding:20px 32px; text-align:center; border-top:1px solid #E2E8F0;">
        <p style="margin:0; font-size:12px; color:#94A3B8;">PLAYBOOK AI Agent Security • Judge Layer</p>
        <p style="margin:6px 0 0 0; font-size:11px; color:#CBD5E1;">{ts}</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def swarm_alert_html(
    swarm_id: str,
    agent_id: str,
    action_summary: str,
    verdict: str,
    timestamp: Optional[str] = None,
    dashboard_url: str = "https://playbooksoar.aiproofofconcept.in/incidents",
) -> str:
    """Render an agent swarm action alert email."""
    color = "#DC2626" if verdict in ("DENY", "BLOCK") else "#16A34A"
    ts = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Swarm Alert</title></head>
<body style="margin:0; padding:0; background:#F1F5F9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F1F5F9;">
  <tr><td align="center" style="padding:40px 16px;">
    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px; width:100%; background:#FFFFFF; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
      <tr><td style="background:#0F172A; padding:28px 32px; text-align:center;">
        <p style="margin:0; font-size:20px; font-weight:800; color:#FFFFFF; letter-spacing:1px;">PLAYBOOK</p>
        <p style="margin:6px 0 0 0; font-size:11px; color:#94A3B8; text-transform:uppercase; letter-spacing:2px;">Agent Swarm Alert</p>
      </td></tr>
      <tr><td style="background:#FEF2F2; border-left:6px solid {color}; padding:24px 32px;">
        <span style="display:inline-block; padding:4px 12px; background:{color}; color:#FFFFFF; border-radius:20px; font-size:11px; font-weight:700; text-transform:uppercase;">{verdict}</span>
        <h1 style="margin:14px 0 0 0; font-size:20px; font-weight:700; color:#111827;">Swarm Agent Blocked</h1>
      </td></tr>
      <tr><td style="padding:28px 32px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom:16px;">
          <tr><td style="padding:4px 0; color:#6B7280; font-size:13px;">Swarm</td><td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right; font-family:monospace;">{swarm_id}</td></tr>
          <tr><td style="padding:4px 0; color:#6B7280; font-size:13px;">Agent</td><td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right;">{agent_id}</td></tr>
          <tr><td style="padding:4px 0; color:#6B7280; font-size:13px;">Action</td><td style="padding:4px 0; color:#111827; font-size:13px; font-weight:600; text-align:right;">{action_summary}</td></tr>
          <tr><td style="padding:4px 0; color:#6B7280; font-size:13px;">Verdict</td><td style="padding:4px 0; color:{color}; font-size:13px; font-weight:700; text-align:right;">{verdict}</td></tr>
        </table>
        <div style="text-align:center; margin-top:24px;">
          <a href="{dashboard_url}" style="display:inline-block; padding:14px 32px; background:#2563EB; color:#FFFFFF; text-decoration:none; border-radius:8px; font-size:14px; font-weight:600;">Open Dashboard →</a>
        </div>
      </td></tr>
      <tr><td style="background:#F8FAFC; padding:20px 32px; text-align:center; border-top:1px solid #E2E8F0;">
        <p style="margin:0; font-size:12px; color:#94A3B8;">PLAYBOOK AI Agent Security • Swarm Monitor</p>
        <p style="margin:6px 0 0 0; font-size:11px; color:#CBD5E1;">{ts}</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def daily_digest_html(
    incidents: list[Dict[str, Any]],
    date: Optional[str] = None,
    dashboard_url: str = "https://playbooksoar.aiproofofconcept.in/dashboard",
) -> str:
    """Render a daily digest email with summary of incidents."""
    ts = date or datetime.utcnow().strftime("%Y-%m-%d")

    rows = ""
    for inc in incidents:
        severity = inc.get("severity", "low")
        color = _severity_color(severity)
        rows += f"""
        <tr>
          <td style="padding:12px; border-bottom:1px solid #E2E8F0; font-family:monospace; font-size:12px; color:#111827;">{inc.get('incident_id', 'N/A')}</td>
          <td style="padding:12px; border-bottom:1px solid #E2E8F0; font-size:12px; color:#374151;">{inc.get('incident_type_name', 'Unknown')}</td>
          <td style="padding:12px; border-bottom:1px solid #E2E8F0; text-align:center;"><span style="display:inline-block; padding:2px 8px; background:{color}; color:#FFF; border-radius:10px; font-size:10px; font-weight:700;">{severity.upper()}</span></td>
          <td style="padding:12px; border-bottom:1px solid #E2E8F0; font-size:12px; color:#6B7280; text-align:right;">{inc.get('agent_id', 'N/A') or 'N/A'}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
          <td colspan="4" style="padding:24px; text-align:center; color:#94A3B8; font-size:14px;">No incidents reported today. All agents operating normally.</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Daily Digest</title></head>
<body style="margin:0; padding:0; background:#F1F5F9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#F1F5F9;">
  <tr><td align="center" style="padding:40px 16px;">
    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px; width:100%; background:#FFFFFF; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08);">
      <tr><td style="background:#0F172A; padding:28px 32px; text-align:center;">
        <p style="margin:0; font-size:20px; font-weight:800; color:#FFFFFF; letter-spacing:1px;">PLAYBOOK</p>
        <p style="margin:6px 0 0 0; font-size:11px; color:#94A3B8; text-transform:uppercase; letter-spacing:2px;">Daily Incident Digest</p>
      </td></tr>
      <tr><td style="padding:28px 32px;">
        <h1 style="margin:0; font-size:18px; font-weight:700; color:#111827;">{ts}</h1>
        <p style="margin:8px 0 20px 0; font-size:14px; color:#6B7280;">{len(incidents)} incident(s) captured in the last 24 hours.</p>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;">
          <thead>
            <tr style="background:#F8FAFC;">
              <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #E2E8F0;">ID</th>
              <th style="padding:10px 12px; text-align:left; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #E2E8F0;">Type</th>
              <th style="padding:10px 12px; text-align:center; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #E2E8F0;">Severity</th>
              <th style="padding:10px 12px; text-align:right; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #E2E8F0;">Agent</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
        <div style="margin-top:24px; text-align:center;">
          <a href="{dashboard_url}" style="display:inline-block; padding:14px 32px; background:#2563EB; color:#FFFFFF; text-decoration:none; border-radius:8px; font-size:14px; font-weight:600;">Open Dashboard →</a>
        </div>
      </td></tr>
      <tr><td style="background:#F8FAFC; padding:20px 32px; text-align:center; border-top:1px solid #E2E8F0;">
        <p style="margin:0; font-size:12px; color:#94A3B8;">PLAYBOOK AI Agent Security • Daily Digest</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""
