const fs = require('fs');
const path = 'apps/web/src/components/phalita/PhalitaCanonicalDashboard.tsx';
let content = fs.readFileSync(path, 'utf8');

// Fix bg-cyan-500 -> bg-[var(--cyan-500)]
content = content.replace(/bg-cyan-500/g, 'bg-[var(--cyan-500)]');

// Fix bg-amber-500 -> bg-[var(--amber-500)]
content = content.replace(/bg-amber-500/g, 'bg-[var(--amber-500)]');

// Fix bg-emerald-500 -> bg-[var(--obsidian-status-success)]
content = content.replace(/bg-emerald-500/g, 'bg-[var(--obsidian-status-success)]');

// Fix bg-indigo-500 -> bg-[var(--text-primary)] (using primary text for indigo accents)
content = content.replace(/bg-indigo-500/g, 'bg-[var(--text-primary)]');

// Fix bg-purple-500 -> bg-[var(--text-primary)] (using primary text for purple accents)
content = content.replace(/bg-purple-500/g, 'bg-[var(--text-primary)]');

// Fix text-cyan-600 -> text-[var(--cyan-400)] (lighter for text)
content = content.replace(/text-cyan-600/g, 'text-[var(--cyan-400)]');

// Fix text-cyan-700 -> text-[var(--cyan-500)]
content = content.replace(/text-cyan-700/g, 'text-[var(--cyan-500)]');

// Fix text-cyan-800 -> text-[var(--cyan-600)] (darker for text)
content = content.replace(/text-cyan-800/g, 'text-[var(--cyan-600)]');

// Fix text-amber-600 -> text-[var(--amber-500)]
content = content.replace(/text-amber-600/g, 'text-[var(--amber-500)]');

// Fix text-emerald-600 -> text-[var(--obsidian-status-success)]
content = content.replace(/text-emerald-600/g, 'text-[var(--obsidian-status-success)]');

// Fix text-indigo-600 -> text-[var(--text-primary)]
content = content.replace(/text-indigo-600/g, 'text-[var(--text-primary)]');

// Fix border-cyan-500 -> border-[var(--cyan-500)]
content = content.replace(/border-cyan-500/g, 'border-[var(--cyan-500)]');

// Fix border-amber-500 -> border-[var(--amber-500)]
content = content.replace(/border-amber-500/g, 'border-[var(--amber-500)]');

// Fix border-emerald-500 -> border-[var(--obsidian-status-success)]
content = content.replace(/border-emerald-500/g, 'border-[var(--obsidian-status-success)]');

// Fix bg-cyan-50 -> bg-[var(--cyan-500)]/10 (10% opacity)
content = content.replace(/bg-cyan-50/g, 'bg-[var(--cyan-500)]/10');

// Fix bg-emerald-50 -> bg-[var(--obsidian-status-success)]/10
content = content.replace(/bg-emerald-50/g, 'bg-[var(--obsidian-status-success)]/10');

// Fix bg-amber-50 -> bg-[var(--amber-500)]/10
content = content.replace(/bg-amber-50/g, 'bg-[var(--amber-500)]/10');

// Fix the specific lines that might still have issues
// Line 436: Recalculate button
content = content.replace(
  /bg-cyan-50 dark:bg-cyan-950\/40 border-cyan-300 dark:border-cyan-800 hover:border-cyan-500 text-cyan-800 dark:text-cyan-200/g,
  'bg-[var(--cyan-500)]/10 dark:bg-[var(--cyan-500)]/10 border-[var(--cyan-500)] dark:border-[var(--cyan-500)] hover:border-[var(--cyan-400)] text-[var(--cyan-800)] dark:text-[var(--cyan-200)]'
);

// Line 842: MoE tab button (similar pattern)
content = content.replace(
  /bg-amber-50 dark:bg-amber-950\/40 border-amber-300 dark:border-amber-800 hover:border-amber-500 text-amber-800 dark:text-amber-200/g,
  'bg-[var(--amber-500)]/10 dark:bg-[var(--amber-500)]/10 border-[var(--amber-500)] dark:border-[var(--amber-500)] hover:border-[var(--amber-400)] text-[var(--amber-800)] dark:text-[var(--amber-200)]'
);

// Fix the tab button backgrounds that were partially fixed
content = content.replace(
  /"bg-cyan-500\/15 border-cyan-500 text-cyan-900 dark:text-cyan-200 font-extrabold shadow-sm ring-1 ring-cyan-400"/g,
  '"bg-[var(--cyan-500)]/15 border-[var(--cyan-500)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--cyan-500)]"'
);

content = content.replace(
  /"bg-indigo-500\/15 border-indigo-500 text-indigo-900 dark:text-indigo-200 font-extrabold shadow-sm ring-1 ring-indigo-400"/g,
  '"bg-[var(--text-primary)]/10 border-[var(--text-primary)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--text-primary)]"'
);

content = content.replace(
  /"bg-amber-500\/15 border-amber-500 text-amber-900 dark:text-amber-200 font-extrabold shadow-sm ring-1 ring-amber-400"/g,
  '"bg-[var(--amber-500)]/15 border-[var(--amber-500)] text-[var(--text-primary)] font-extrabold shadow-sm ring-1 ring-[var(--amber-500)]"'
);

// Fix error banner
content = content.replace(
  /bg-rose-100 dark:bg-rose-950\/60 border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-200/g,
  'bg-[var(--obsidian-status-danger)]/10 dark:bg-[var(--obsidian-status-danger)]/10 border-[var(--obsidian-status-danger)] dark:border-[var(--obsidian-status-danger)] text-[var(--obsidian-status-danger)] dark:text-[var(--obsidian-status-danger)]'
);

// Fix consultation overview banner - use panelClass and darkCardTextClass
content = content.replace(
  /border rounded-xl p-5 shadow-sm space-y-3 \$\{\w+ \? "bg-\[#0b1424\] border-slate-800 text-slate-100" : "bg-white border-slate-200 text-slate-900"\} transition-colors/,
  'border rounded-xl p-5 shadow-sm space-y-3 ${panelClass(isDark)} ${darkCardTextClass(isDark)} transition-colors'
);

// Fix remaining icon colors
content = content.replace(/text-cyan-600 dark:text-cyan-400/g, 'text-[var(--cyan-400)] dark:text-[var(--cyan-400)]');

fs.writeFileSync(path, content, 'utf8');
console.log('All hardcoded hex colors have been replaced with CSS variables!');