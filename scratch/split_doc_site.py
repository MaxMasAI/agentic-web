import os

file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Architecture_Doc_site", "index.html")
out_dir = os.path.dirname(file_path)

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

style_start_tag = "<style>"
style_end_tag = "</style>"
script_start_tag = "<script>"
script_end_tag = "</script>"

s_start = content.find(style_start_tag)
s_end = content.find(style_end_tag)

sc_start = content.find(script_start_tag)
sc_end = content.find(script_end_tag)

print(f"s_start={s_start}, s_end={s_end}, sc_start={sc_start}, sc_end={sc_end}")

if s_start != -1 and s_end != -1 and sc_start != -1 and sc_end != -1:
    css_content = content[s_start + len(style_start_tag):s_end].strip()
    js_content = content[sc_start + len(script_start_tag):sc_end].strip()

    css_file = os.path.join(out_dir, "styles.css")
    with open(css_file, "w", encoding="utf-8") as f:
        f.write(css_content + "\n")

    js_file = os.path.join(out_dir, "script.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(js_content + "\n")

    html_content = (
        content[:s_start] +
        '<link rel="stylesheet" href="styles.css" />' +
        content[s_end + len(style_end_tag):sc_start] +
        '<script src="script.js"></script>' +
        content[sc_end + len(script_end_tag):]
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("SPLIT_SUCCESS")
else:
    print("FAILED TO FIND TAGS")
