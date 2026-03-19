import os
import re

for root, _, files in os.walk("/home/williams.sobrinho@saude.local/src/sistema_qualivida/front/src/templates"):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    for char in line:
                        if not char.isascii() and ord(char) > 0x2500:
                            print(f"{path}:{i+1}: {line.strip()}")
                            break
