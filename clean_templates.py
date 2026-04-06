import os
import re

def clean_html(content):
    # Remove animation classes
    content = content.replace(' reveal', '')
    content = content.replace('reveal ', '')
    content = content.replace(' reveal-stagger', '')
    content = content.replace('reveal-child', '')
    content = content.replace('label-wipe', '')
    content = content.replace('badge-pop', '')
    content = content.replace('radar-spin', '')
    content = content.replace('btn-shimmer', '')
    content = content.replace('shield-beat', '')
    content = content.replace('float-anim', '')
    content = content.replace('heartbeat-line', '')
    content = content.replace('shadow-glow', '')
    
    # Remove data-reveal and data-delay attributes
    content = re.sub(r'\sdata-reveal="[^"]*"', '', content)
    content = re.sub(r'\sdata-delay="[^"]*"', '', content)
    content = re.sub(r'\sdata-counter', '', content)
    content = re.sub(r'\sdata-target="[^"]*"', '', content)
    
    return content

templates_dir = r"c:\Users\USER\Downloads\Telegram Desktop\SmartHealth-AI\SmartHealth-AI\app\templates"

for filename in os.listdir(templates_dir):
    if filename.endswith(".html"):
        path = os.path.join(templates_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned = clean_html(content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Cleaned {filename}")
