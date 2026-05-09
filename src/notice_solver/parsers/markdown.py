from markdownify import markdownify as md


def html_to_markdown(html: str) -> str:
    if not html:
        return ""
    result = md(
        html,
        heading_style="ATX",
        bullets="-",
        strip=["img"],
    )
    return result.strip()
