import os
import re

dir_path = "/home/williams.sobrinho@saude.local/src/sistema_qualivida/front/src/templates"

for root, dirs, files in os.walk(dir_path):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r') as file:
                content = file.read()
            
            def replacer(match):
                cls_str = match.group(0)
                # Ensure it has hover:text- or group-hover:text-
                hover_match = re.search(r'(?:group-)?hover:text-([a-z]+(?:-[0-9]+)?)', cls_str)
                if hover_match:
                    active_col = 'text-' + hover_match.group(1)
                    # Replace the faded colors
                    cls_str = re.sub(r'text-(?:slate|gray)-(?:300|400|500)(?!\w)', active_col, cls_str)
                    return cls_str
                return cls_str

            new_content = re.sub(r'class="[^"]*"', replacer, content)
            
            if new_content != content:
                with open(filepath, 'w') as file:
                    file.write(new_content)
                print(f"Updated {f}")

