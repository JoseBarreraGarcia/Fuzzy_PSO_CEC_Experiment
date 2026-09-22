"""
Fix UTF-8 mojibake in wea_analysis.py caused by PowerShell CP1252 read/write.

Each multi-byte UTF-8 arrow char was read as individual CP1252 chars and
written back, turning single-char arrows into 2-3 char garbled sequences.

Mapping (CP1252 reinterpretation of UTF-8 bytes → correct Unicode):
  â†"  (U+00E2 U+2020 U+201C)  ←  UTF-8 E2 86 93  →  ↓  U+2193
  â†'  (U+00E2 U+2020 U+2018)  ←  UTF-8 E2 86 91  →  ↑  U+2191
  â€"  (U+00E2 U+20AC U+201D)  ←  UTF-8 E2 80 94  →  —  U+2014  (em dash)
  â†'  (U+00E2 U+2020 U+2019)  ←  UTF-8 E2 86 92  →  →  U+2192
  â†\x90 (U+00E2 U+2020 U+0090) ← UTF-8 E2 86 90  →  ←  U+2190
  â†"  (U+00E2 U+2020 U+201D)  ←  UTF-8 E2 86 94  →  ↔  U+2194
  Ã—  (U+00C3 U+2014)          ←  UTF-8 C3 97     →  ×  U+00D7
  Ã€  (U+00C3 U+20AC)          ←  could be various; handled if found
"""

from pathlib import Path

TARGET = Path(__file__).parent / 'wea_analysis.py'

with open(TARGET, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

original_len = len(content)

# Order matters: longer/more specific sequences first.
replacements = [
    # --- 3-byte arrow sequences (all start with â† = U+00E2 U+2020) ---
    ('\u00e2\u2020\u201c', '\u2193'),   # â†"  →  ↓  (down,   E2 86 93)
    ('\u00e2\u2020\u2018', '\u2191'),   # â†'  →  ↑  (up,     E2 86 91)
    ('\u00e2\u2020\u2019', '\u2192'),   # â†'  →  →  (right,  E2 86 92)
    ('\u00e2\u2020\u0090', '\u2190'),   # â†\x90 → ←  (left,   E2 86 90)
    ('\u00e2\u2020\u201d', '\u2194'),   # â†"  →  ↔  (bidi,   E2 86 94)
    # --- em dash (starts with â€ = U+00E2 U+20AC) ---
    ('\u00e2\u20ac\u201d', '\u2014'),   # â€"  →  —  (em dash, E2 80 94)
    # --- multiplication sign (C3 97 → Ã + CP1252[0x97]=em dash) ---
    ('\u00c3\u2014',        '\u00d7'),   # Ã—  →  ×  (C3 97)
    # --- any remaining â† 2-char fragment without resolved 3rd byte ---
    ('\u00e2\u2020',        '\u2191'),   # fallback: â† alone → ↑ (safest guess)
]

report = []
for old, new in replacements:
    count = content.count(old)
    if count:
        content = content.replace(old, new)
        report.append(f'  {count:3d}x  {repr(old)}  →  {repr(new)}')

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Fixed {TARGET.name}:')
for line in report:
    print(line)
if not report:
    print('  No garbled sequences found (file already clean).')
print(f'File length: {original_len} → {len(content)} chars')
