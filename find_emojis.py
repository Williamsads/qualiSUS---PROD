import os
import re

emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
directory = "/home/williams.sobrinho@saude.local/src/sistema_qualivida/front/src/templates"

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if emoji_pattern.search(line):
                        print(f"{path}:{i+1}: {line.strip()}")
