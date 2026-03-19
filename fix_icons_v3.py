import os
import re

dir_path = "/home/williams.sobrinho@saude.local/src/sistema_qualivida/front/src/templates"

def fix_icons_in_html(content):
    # Rule 1: Find <i data-lucide="..." class="... text-slate-400 ...">
    # Replace the faded text color with text-brand-600
    
    def i_replacer(match):
        full_tag = match.group(0)
        # Check if it has a faded color
        faded_match = re.search(r'text-(slate|gray)-(300|400|500)', full_tag)
        if faded_match:
            # Replace it with text-brand-600
            new_tag = re.sub(r'text-(slate|gray)-(300|400|500)(?!\w)', 'text-brand-600', full_tag)
            return new_tag
        return full_tag

    # Rule 2: Find <button ... class="... text-slate-400 ... hover:text-brand-600 ...">
    def button_replacer(match):
        full_tag = match.group(0)
        faded_match = re.search(r'text-(slate|gray)-(300|400|500)', full_tag)
        hover_match = re.search(r'hover:text-([a-z]+-\d+)', full_tag)
        
        if faded_match and hover_match:
            active_color = 'text-' + hover_match.group(1)
            new_tag = re.sub(r'text-(slate|gray)-(300|400|500)(?!\w)', active_color, full_tag)
            return new_tag
        elif faded_match and ('data-lucide' in full_tag or '<i ' in full_tag or 'icon' in full_tag):
             new_tag = re.sub(r'text-(slate|gray)-(300|400|500)(?!\w)', 'text-brand-600', full_tag)
             return new_tag
        return full_tag

    content = re.sub(r'<i\s+[^>]*data-lucide[^>]*>', i_replacer, content)
    # also standard <i> tags if they have text-slate-400
    content = re.sub(r'<i\s+class="[^"]*text-(slate|gray)-(300|400|500)[^"]*"[^>]*>', lambda m: re.sub(r'text-(slate|gray)-(300|400|500)', 'text-brand-600', m.group(0)), content)
    
    # buttons that wrap icons or have hover states
    content = re.sub(r'<button\s+[^>]*class="[^"]*"[^>]*>', button_replacer, content)
    content = re.sub(r'<a\s+[^>]*class="[^"]*"[^>]*>', button_replacer, content)
    
    return content

for root, dirs, files in os.walk(dir_path):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r') as file:
                content = file.read()
            
            new_content = fix_icons_in_html(content)
            
            if new_content != content:
                with open(filepath, 'w') as file:
                    file.write(new_content)
                print(f"Updated {f}")
