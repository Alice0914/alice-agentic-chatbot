import os
import re
import pickle

INDEX_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_index", "index.pkl")
NEW_NAME = "AI Engineering 2025 490P"

with open(INDEX_FILE, "rb") as f:
    data = pickle.load(f)

texts = data["texts"]
print(f"Loaded {len(texts)} chunks", flush=True)

pattern = re.compile(rf"\[Source: {re.escape(NEW_NAME)}, Page (-?\d+)\]")
updated = 0
new_texts = []
for t in texts:
    def replace(m):
        page = int(m.group(1))
        if page <= 0:
            return f"[Source: {NEW_NAME}, Front matter]"
        return f"[Source: {NEW_NAME}, Page {page}]"
    new_t, n = pattern.subn(replace, t)
    if n > 0:
        updated += 1
    new_texts.append(new_t)

print(f"Updated {updated} chunks", flush=True)

data["texts"] = new_texts
with open(INDEX_FILE, "wb") as f:
    pickle.dump(data, f)
print("Index saved.", flush=True)

print("\nSample chunks:")
for marker in ["Front matter", "Page 3", "Page 27"]:
    for t in new_texts:
        if marker in t:
            print(f"  {t[:120]}...")
            break
