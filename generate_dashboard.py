#!/usr/bin/env python3
"""
AstroOS Phase I Pipeline Dashboard Generator

Reads tasks_data.json and generates a self-contained HTML dashboard
with real-time progress tracking and dependency visualization.

Usage:
    python generate_dashboard.py

Output:
    vistara_pipeline_progress.html
"""

import json
from datetime import datetime
from pathlib import Path

# Design tokens - distinctive Vistara identity
COLORS = {
    'bg': '#f8fafc',
    'card': '#ffffff',
    'border': '#e2e8f0',
    'text': '#1e293b',
    'text2': '#64748b',
    'accent': '#2563eb',
    'accent-light': '#dbeafe',
    'green': '#16a34a',
    'green-light': '#dcfce7',
    'amber': '#d97706',
    'amber-light': '#fef3c7',
    'red': '#dc2626',
    'red-light': '#fee2e2',
}

# Status configuration
STATUS_CONFIG = {
    'pending': {
        'label': 'Pending',
        'badge_bg': COLORS['border'],
        'badge_text': COLORS['text2'],
        'tag_bg': COLORS['border'],
        'tag_text': COLORS['text2'],
        'opacity': 0.5
    },
    'in_progress': {
        'label': 'In Progress',
        'badge_bg': COLORS['accent'],
        'badge_text': '#ffffff',
        'tag_bg': COLORS['accent-light'],
        'tag_text': COLORS['accent'],
        'opacity': 1.0,
        'animate': True
    },
    'completed': {
        'label': 'Done',
        'badge_bg': COLORS['green'],
        'badge_text': '#ffffff',
        'tag_bg': COLORS['green-light'],
        'tag_text': COLORS['green'],
        'opacity': 1.0
    }
}

TASK_ICONS = {
    1: '📋',   # Governance
    6: '📚',   # Docs
    7: '🧮',   # Calc
    8: '🎨',   # UI
    11: '🔬',  # Research
    12: '🧘',  # Yoga
    13: '✅',  # QA
    14: '🔒',  # Governance enforcement
    15: '🏷️',  # Release
}


def load_data():
    """Load task data from JSON file."""
    data_path = Path(__file__).parent / 'tasks_data.json'
    with open(data_path, 'r') as f:
        return json.load(f)


def calculate_progress(tasks):
    """Calculate completion percentage."""
    total = len(tasks)
    completed = sum(1 for t in tasks if t['status'] == 'completed')
    return round((completed / total * 100) if total > 0 else 0, 1)


def status_color(status):
    """Return CSS color variables for a given status."""
    cfg = STATUS_CONFIG[status]
    return {
        'badge_bg': cfg['badge_bg'],
        'badge_text': cfg['badge_text'],
        'tag_bg': cfg['tag_bg'],
        'tag_text': cfg['tag_text']
    }


def generate_task_item(task, idx):
    """Generate HTML for a single task item."""
    colors = status_color(task['status'])
    icon = TASK_ICONS.get(task['id'], '•')
    cfg = STATUS_CONFIG[task['status']]

    has_deps = len(task.get('dependencies', [])) > 0
    has_blocks = len(task.get('blocks', [])) > 0

    # Build dependency/blocking indicators
    dep_html = ''
    if has_deps:
        dep_ids = ', '.join(f'#{d}' for d in task['dependencies'])
        dep_html = f'<div class="dep-indicator" title="Blocked by: {dep_ids}">⏳ {dep_ids}</div>'

    if has_blocks:
        block_ids = ', '.join(f'#{b}' for b in task['blocks'])
        dep_html += f'<div class="block-indicator" title="Blocks: {block_ids}">🔗 {block_ids}</div>'

    # Status class
    status_class = task['status']
    if cfg.get('animate'):
        status_class += ' pulse'

    return f'''    <div class="task {status_class}" data-id="{task['id']}" style="opacity: {cfg['opacity']};">
      <div class="badge" style="background: {colors['badge_bg']}; color: {colors['badge_text']};">
        {icon}
      </div>
      <div class="info">
        <div class="title">#{task['id']} {task['label']}</div>
        <div class="owner">{task['owner']}</div>
        <div class="dep-chain">{dep_html}</div>
      </div>
      <span class="status-tag" style="background: {colors['tag_bg']}; color: {colors['tag_text']};">
        {cfg['label']}
      </span>
    </div>'''


def generate_html(data):
    """Generate complete HTML document."""
    tasks = data['tasks']
    meta = data['metadata']
    progress = calculate_progress(tasks)

    task_items = '\n'.join(generate_task_item(t, i) for i, t in enumerate(tasks))

    # Phase completion summary
    completed_phases = data.get('phases_completed', {})
    phase_summary = ''
    if completed_phases:
        phase_list = ', '.join(f'{k} ({v})' for k, v in completed_phases.items())
        phase_summary = f'<div class="phases-complete">Phases complete: {phase_list}</div>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta['title']}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    color-scheme: light;
    --bg: {COLORS['bg']};
    --card: {COLORS['card']};
    --border: {COLORS['border']};
    --text: {COLORS['text']};
    --text2: {COLORS['text2']};
    --accent: {COLORS['accent']};
    --green: {COLORS['green']};
    --amber: {COLORS['amber']};
    --red: {COLORS['red']};
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    max-width: 720px;
    margin: 0 auto;
    line-height: 1.5;
  }}
  h1 {{
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 10px;
    letter-spacing: -0.02em;
  }}
  .subtitle {{
    font-size: 14px;
    color: var(--text2);
    margin-bottom: 20px;
  }}
  .bar {{
    display: flex;
    height: 10px;
    background: var(--border);
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 24px;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
  }}
  .bar-fill {{
    background: var(--accent);
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    position: relative;
  }}
  .bar-fill::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg,
      rgba(255,255,255,0) 0%,
      rgba(255,255,255,0.15) 50%,
      rgba(255,255,255,0) 100%);
    animation: shimmer 2s infinite;
  }}
  @keyframes shimmer {{
    0% {{ transform: translateX(-100%); }}
    100% {{ transform: translateX(100%); }}
  }}
  .bar-fill.done {{ background: var(--green); }}
  .task {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .task:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-1px);
  }}
  .task.pending {{ opacity: 0.55; }}
  .task.in_progress {{
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent), 0 4px 12px rgba(37, 99, 235, 0.12);
  }}
  .task.completed {{
    border-color: var(--green);
    box-shadow: 0 0 0 1px var(--green), 0 4px 12px rgba(22, 163, 74, 0.12);
  }}
  .badge {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
    flex-shrink: 0;
    background: var(--border);
    color: var(--text2);
    transition: transform 0.2s;
  }}
  .task:hover .badge {{
    transform: scale(1.05);
  }}
  .task.in_progress .badge {{
    background: var(--accent);
    color: #fff;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
  }}
  .task.completed .badge {{
    background: var(--green);
    color: #fff;
  }}
  .task .info {{
    flex: 1;
    min-width: 0;
  }}
  .task .title {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.3;
  }}
  .task .owner {{
    font-size: 12px;
    color: var(--text2);
    margin-top: 4px;
    font-weight: 500;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .dep-indicator, .block-indicator {{
    display: inline-block;
    font-size: 10px;
    background: var(--amber-light);
    color: var(--amber);
    padding: 2px 6px;
    border-radius: 4px;
    margin-top: 6px;
    font-weight: 500;
    letter-spacing: 0.3px;
  }}
  .block-indicator {{
    background: var(--accent-light);
    color: var(--accent);
    margin-left: 6px;
  }}
  .status-tag {{
    font-size: 11px;
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: 600;
    background: var(--border);
    color: var(--text2);
    white-space: nowrap;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .task.in_progress .status-tag {{
    animation: pulse 2s infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.7; }}
  }}
  .footer {{
    margin-top: 28px;
    font-size: 12px;
    color: var(--text2);
    text-align: center;
    border-top: 1px solid var(--border);
    padding-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .footer .source {{
    font-family: monospace;
    font-size: 11px;
    opacity: 0.7;
  }}
  .footer .generated {{
    font-style: italic;
  }}
  .phases-complete {{
    font-size: 12px;
    color: var(--green);
    margin-bottom: 8px;
    padding: 8px 12px;
    background: var(--green-light);
    border-radius: 6px;
    font-weight: 500;
  }}
  .created-by {{
    font-size: 11px;
    color: var(--text2);
    margin-top: 8px;
    opacity: 0.8;
  }}
</style>
</head>
<body>
<h1>{meta['title']}</h1>
<div class="subtitle">{meta['subtitle']}</div>
<div class="phases-complete">{phase_summary}</div>
<div class="bar"><div class="bar-fill" id="progressBar" style="width: {progress}%"></div></div>
<div id="taskList">
{task_items}
</div>
<div class="footer">
  <div>Scheduled: <strong>astroos-phase-i-orchestrator-v2</strong> · Auto-updates on refresh</div>
  <div class="source">Source: {meta['source']}</div>
  <div class="generated">Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
  <div class="created-by">Created with generate_dashboard.py — local, offline, reproducible</div>
</div>

<script>
// Restore saved task state from localStorage (if any)
const saved = JSON.parse(localStorage.getItem('vistara_progress') || '{{}}');
const tasks = {json.dumps(tasks)};

// Apply saved statuses
tasks.forEach(t => {{
  if(saved[t.id] && ['pending','in_progress','completed'].includes(saved[t.id])) {{
    t.status = saved[t.id];
  }}
}});

function render() {{
  const list = document.getElementById('taskList');
  const done = tasks.filter(t => t.status==='completed').length;
  const total = tasks.length;
  document.getElementById('progressBar').style.width = (done/total*100)+'%';

  list.innerHTML = tasks.map(t => {{
    const cfg = STATUS_CONFIG[t.status];
    const icon = TASK_ICONS[t.id] || '•';
    const hasDeps = t.dependencies && t.dependencies.length > 0;
    const hasBlocks = t.blocks && t.blocks.length > 0;
    let depHtml = '';
    if(hasDeps) {{
      depHtml += `<div class="dep-indicator" title="Blocked by: ${{t.dependencies.join(', ')}}">⏳ ${{t.dependencies.map(d=>'#'+d).join(', ')}}</div>`;
    }}
    if(hasBlocks) {{
      depHtml += `<div class="block-indicator" title="Blocks: ${{t.blocks.join(', ')}}">🔗 ${{t.blocks.map(b=>'#'+b).join(', ')}}</div>`;
    }}
    return `<div class="task ${{t.status}} ${{cfg.animate?'pulse':''}}" data-id="${{t.id}}" style="opacity: ${{cfg.opacity}};">
      <div class="badge" style="background: ${{cfg.badge_bg}}; color: ${{cfg.badge_text}};">${{icon}}</div>
      <div class="info">
        <div class="title">#${{t.id}} ${{t.label}}</div>
        <div class="owner">${{t.owner}}</div>
        <div class="dep-chain">${{depHtml}}</div>
      </div>
      <span class="status-tag" style="background: ${{cfg.tag_bg}}; color: ${{cfg.tag_text}};">${{cfg.label}}</span>
    </div>`;
  }}).join('');
}}

// Status cycle on click (for local testing)
document.addEventListener('click', e => {{
  const taskEl = e.target.closest('.task');
  if(!taskEl) return;
  const id = parseInt(taskEl.dataset.id);
  const statuses = ['pending','in_progress','completed'];
  const current = tasks.find(t=>t.id===id).status;
  const next = statuses[(statuses.indexOf(current)+1)%3];
  tasks.find(t=>t.id===id).status = next;
  localStorage.setItem('vistara_progress', JSON.stringify(
    Object.fromEntries(tasks.map(t=>[t.id, t.status]))
  ));
  render();
}};

render();
</script>
</body>
</html>'''

def main():
    data = load_data()
    html = generate_html(data)
    out_path = Path(__file__).parent / 'vistara_pipeline_progress.html'
    with open(out_path, 'w') as f:
        f.write(html)
    print(f'✓ Dashboard generated: {out_path}')
    print(f'  Tasks: {len(data["tasks"])}')
    print(f'  Completed: {sum(1 for t in data["tasks"] if t["status"]=="completed")}')
    print(f'  Progress: {calculate_progress(data["tasks"])}%')
    print('  Open in browser: file://' + str(out_path.resolve()))

if __name__ == '__main__':
    main()
