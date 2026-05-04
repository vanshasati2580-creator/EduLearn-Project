"""Simulate what video_for_topic does for Python course lessons."""
import json, os, re

# Load the topic map exactly as app.py does
def load_video_topic_map():
    path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'video_topics_map.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {k.lower(): v for k, v in data.items()}
    except Exception as e:
        print(f"Error loading topic map: {e}")
    return {}

topic_map = load_video_topic_map()
print(f"Topic map loaded, {len(topic_map)} entries")
print()

# Simulate the lookup for Python course modules
MODULES = [
    'Python Syntax and REPL', 'Variables and Data Types', 'Control Flow', 'Functions',
    'Data Structures (Lists, Dicts, Sets)', 'Modules and Packages', 'File I/O and Errors', 'OOP Basics',
    'Virtual Environments and CLI Apps', 'Mini Projects and Best Practices'
]

cat_key = 'python'
course_title = 'Python for Beginners'

for i, mod in enumerate(MODULES):
    # This is what video_for_topic does
    key_variants = [
        f"{cat_key}::{mod}".lower(),
        mod.lower(),
    ]
    found = False
    for kv in key_variants:
        if kv in topic_map:
            url = topic_map[kv]
            print(f"Lesson {i+1}: {mod}")
            print(f"  Key matched: '{kv}'")
            print(f"  URL: {url}")
            found = True
            break
    if not found:
        print(f"Lesson {i+1}: {mod}")
        print(f"  NO MATCH for keys: {key_variants}")
        print(f"  Would use youtube_search_embed fallback")
