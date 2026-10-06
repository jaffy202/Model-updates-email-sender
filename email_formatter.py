import re


# ── Provider colour palette (inline CSS, email-safe) ────────────────────────
PROVIDER_COLORS = {
    "openai":    {"bg": "#10a37f", "text": "#ffffff"},
    "anthropic": {"bg": "#c96442", "text": "#ffffff"},
    "xai":       {"bg": "#7c3aed", "text": "#ffffff"},
    "google":    {"bg": "#4285f4", "text": "#ffffff"},
    "meta":      {"bg": "#0866ff", "text": "#ffffff"},
    "mistral":   {"bg": "#f97316", "text": "#ffffff"},
    "xiaomi":    {"bg": "#ff6900", "text": "#ffffff"},
    "cohere":    {"bg": "#39594d", "text": "#ffffff"},
    "deepseek":  {"bg": "#0ea5e9", "text": "#ffffff"},
}
DEFAULT_COLOR = {"bg": "#475569", "text": "#ffffff"}


def _get_provider_colors(lead: str) -> dict:
    """Return colour dict for the provider mentioned in the lead sentence."""
    lead_lower = lead.lower()
    for provider, colors in PROVIDER_COLORS.items():
        if provider in lead_lower:
            return colors
    return DEFAULT_COLOR


def _extract_provider(lead: str) -> str:
    """Extract the provider name from the lead sentence (e.g. 'from OpenAI')."""
    match = re.search(r"from ([A-Za-z0-9_\-\.]+)", lead)
    return match.group(1) if match else "Unknown"


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_models(raw_text: str) -> list[dict]:
    """
    Parse the raw scraper output into a list of model dicts.
    Each dict has keys: name, lead, description, provider, colors.
    """
    models = []
    # Split on blank lines that precede a "Model:" line
    blocks = re.split(r"\n(?=Model:)", raw_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        model: dict = {"name": "", "lead": "", "description": "", "provider": "", "colors": DEFAULT_COLOR}

        name_match = re.search(r"^Model:\s*(.+)$", block, re.MULTILINE)
        lead_match = re.search(r"^Lead:\s*(.+)$", block, re.MULTILINE)
        desc_match = re.search(r"^Description:\s*(.+)$", block, re.MULTILINE | re.DOTALL)

        if name_match:
            model["name"] = name_match.group(1).strip()
        if lead_match:
            model["lead"] = lead_match.group(1).strip()
            model["provider"] = _extract_provider(model["lead"])
            model["colors"] = _get_provider_colors(model["lead"])
        if desc_match:
            # Description may be followed by another field — stop before Lead/Model
            desc_raw = desc_match.group(1)
            desc_clean = re.split(r"\n(?:Model|Lead):", desc_raw)[0].strip()
            model["description"] = desc_clean

        if model["name"]:
            models.append(model)

    return models


# ── HTML builder ─────────────────────────────────────────────────────────────

def build_html_email(models: list[dict], date_str: str) -> str:
    """Return a complete HTML email string with inline CSS."""

    cards_html = ""
    for m in models:
        bg    = m["colors"]["bg"]
        fg    = m["colors"]["text"]
        name  = m["name"]
        lead  = m["lead"]
        desc  = m["description"]
        prov  = m["provider"]

        card = f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="margin-bottom:20px; border-radius:8px; overflow:hidden;
                      box-shadow:0 2px 6px rgba(0,0,0,0.12); font-family:Arial,sans-serif;">
          <!-- Header -->
          <tr>
            <td style="background:{bg}; padding:14px 20px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="color:{fg}; font-size:18px; font-weight:bold;">{name}</td>
                  <td align="right" style="color:{fg}; font-size:12px; opacity:0.85;
                                           white-space:nowrap;">{prov}</td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Lead -->
          <tr>
            <td style="background:#f8fafc; padding:14px 20px;
                       border-left:4px solid {bg};
                       color:#1e293b; font-size:14px; font-weight:bold;
                       line-height:1.5;">
              {lead}
            </td>
          </tr>
          <!-- Description -->
          <tr>
            <td style="background:#ffffff; padding:14px 20px;
                       color:#334155; font-size:13px; line-height:1.7;
                       border-top:1px solid #e2e8f0;">
              {desc}
            </td>
          </tr>
        </table>
        """
        cards_html += card

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LLM Model Updates — {date_str}</title>
</head>
<body style="margin:0; padding:0; background:#f1f5f9; font-family:Arial,sans-serif;">

  <!-- Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#f1f5f9; padding:30px 0;">
    <tr>
      <td align="center">
        <table width="640" cellpadding="0" cellspacing="0" border="0"
               style="max-width:640px; width:100%;">

          <!-- Header banner -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e293b 0%,#334155 100%);
                       border-radius:10px 10px 0 0; padding:28px 30px;">
              <p style="margin:0; color:#94a3b8; font-size:12px;
                         text-transform:uppercase; letter-spacing:1.5px;">
                Weekly Digest
              </p>
              <h1 style="margin:6px 0 0; color:#f8fafc; font-size:24px; font-weight:700;">
                🤖 LLM Model Updates
              </h1>
              <p style="margin:6px 0 0; color:#94a3b8; font-size:13px;">{date_str}</p>
            </td>
          </tr>

          <!-- Summary bar -->
          <tr>
            <td style="background:#0f172a; padding:12px 30px;">
              <p style="margin:0; color:#cbd5e1; font-size:13px;">
                <strong style="color:#38bdf8;">{len(models)} new model{"s" if len(models) != 1 else ""}</strong>
                &nbsp;- The advancement in AI models.
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:24px 20px;">
              {cards_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#e2e8f0; border-radius:0 0 10px 10px;
                       padding:16px 30px; text-align:center;">
              <p style="margin:0; color:#64748b; font-size:11px; line-height:1.6;">
                Data sourced from
                <a href="https://llm-stats.com/llm-updates" style="color:#0ea5e9;">llm-stats.com</a>
                &nbsp;·&nbsp; You're receiving this because you set up the LLM update tracker.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""

    return html


# ── Plain-text builder ────────────────────────────────────────────────────────

def build_plain_text_email(models: list[dict], date_str: str) -> str:
    """Return a clean, readable plain-text version of the email."""
    divider = "━" * 60
    lines = [
        f"LLM MODEL UPDATES — {date_str}",
        f"{len(models)} new model{'s' if len(models) != 1 else ''} released.",
        "",
    ]

    for m in models:
        lines += [
            divider,
            f"  {m['name']}  ({m['provider']})",
            divider,
            "",
            "SUMMARY",
            m["lead"],
            "",
            "DETAILS",
            m["description"],
            "",
        ]

    lines += [
        divider,
        "Data sourced from https://llm-stats.com/llm-updates",
    ]

    return "\n".join(lines)
