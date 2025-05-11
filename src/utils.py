import markdown
import re

def render_markdown(text):
    # Store LaTeX parts
    placeholders = {}
    count = 0

    # Handle block LaTeX ($$...$$)
    def replace_block(match):
        nonlocal count
        placeholder = f"LATEX_BLOCK_{count}_"
        placeholders[placeholder] = match.group(0)
        count += 1
        return placeholder

    text = re.sub(r'(?<!\\)\$\$(.*?)(?<!\\)\$\$', replace_block, text, flags=re.DOTALL)

    # Handle inline LaTeX ($...$)
    def replace_inline(match):
        nonlocal count
        placeholder = f"LATEX_INLINE_{count}_"
        placeholders[placeholder] = match.group(0)
        count += 1
        return placeholder

    text = re.sub(r'(?<!\\)\$(.*?)(?<!\\)\$', replace_inline, text)

    # Process with markdown
    html = markdown.markdown(text, extensions=['fenced_code', 'codehilite', 'tables', 'md_in_html'])

    # Restore LaTeX parts
    for placeholder, latex in placeholders.items():
        html = html.replace(placeholder, latex)

    return html
