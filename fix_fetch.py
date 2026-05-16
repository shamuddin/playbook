import os
import sys

pages_dir = os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'pages')
for f in os.listdir(pages_dir):
    if not f.endswith('.tsx'):
        continue
    path = os.path.join(pages_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    orig = content
    # Add import if missing
    if 'apiFetch' not in content:
        if "import { getApiBase } from '../utils/config'" in content:
            content = content.replace(
                "import { getApiBase } from '../utils/config'",
                "import { getApiBase } from '../utils/config'\nimport { apiFetch } from '../utils/api'"
            )
        elif "import { apiFetch } from '../utils/api'" not in content:
            # Insert after first import line
            lines = content.split('\n')
            idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import '):
                    idx = i + 1
            lines.insert(idx, "import { apiFetch } from '../utils/api'")
            content = '\n'.join(lines)
    # Replace fetch with apiFetch for API_BASE calls
    content = content.replace('fetch(`${API_BASE}', 'apiFetch(`${API_BASE}')
    if content != orig:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f'Updated {f}')
    else:
        print(f'Skipped {f}')
