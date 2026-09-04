const fs = require('fs');
const path = 'apps/web/src/components/phalita/PhalitaCanonicalDashboard.tsx';
let content = fs.readFileSync(path, 'utf8');

// Fix 1: Current Sky button className
const oldButton = `className={\`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 cursor-pointer text-xs font-mono font-bold transition-all shadow-sm \$\{
              chartProfile.name.includes("Current Sky")
                ? "bg-cyan-500 text-slate-950 border-cyan-400 font-extrabold"
                : "bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-cyan-500"
            }\`}`;
const newButton = `className={\`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 cursor-pointer text-xs font-mono font-bold transition-all shadow-sm \$\{getDarkClass(isDark, "bg-[var(--bg-surface)] border-slate-300 text-slate-700 hover:border-[var(--cyan-500)]", "bg-[var(--bg-card)] border-slate-300 dark:border-slate-700 text-slate-300 hover:border-[var(--cyan-500)]")\}\`}`;

content = content.replace(oldButton, newButton);

// Fix 2: Recalculate button - use CSS vars
content = content.replace(
  /bg-cyan-50 dark:bg-cyan-950\/40 border-cyan-300 dark:border-cyan-800 hover:border-cyan-500 text-cyan-800 dark:text-cyan-200/g,
  'bg-[var(--amber-glow-soft)] dark:bg-[var(--amber-glow-soft)] border-[var(--amber-500)] dark:border-[var(--amber-500)] hover:border-[var(--amber-400)] text-[var(--text-primary)] dark:text-[var(--text-primary)]'
);

// Fix 3: Export Excel button - use CSS vars
content = content.replace(
  /bg-emerald-50 dark:bg-emerald-950\/40 border-emerald-300 dark:border-emerald-800 hover:border-emerald-500 text-emerald-800 dark:text-emerald-200/g,
  'bg-[var(--obsidian-status-success)]/10 dark:bg-[var(--obsidian-status-success)]/10 border-[var(--obsidian-status-success)] dark:border-[var(--obsidian-status-success)] hover:border-[var(--obsidian-status-success)] text-[var(--text-primary)] dark:text-[var(--text-primary)]'
);

// Fix 4: Consultation overview banner background
content = content.replace(
  /<div className={`border rounded-xl p-5 shadow-sm space-y-3 \$\{isDark \? "bg-\[#0b1424\] border-slate-800 text-slate-100" : "bg-white border-slate-200 text-slate-900"\} transition-colors`}>/g,
  '<div className={`border rounded-xl p-5 shadow-sm space-y-3 \$\{panelClass(isDark)\} \$\{darkCardTextClass(isDark)\} transition-colors`}>'
);

// Fix 5: Tab button backgrounds to use CSS vars
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

// Fix 6: Error banner
content = content.replace(
  /bg-rose-100 dark:bg-rose-950\/60 border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-200/g,
  'bg-[var(--obsidian-status-danger)]/10 dark:bg-[var(--obsidian-status-danger)]/10 border-[var(--obsidian-status-danger)] dark:border-[var(--obsidian-status-danger)] text-[var(--obsidian-status-danger)] dark:text-[var(--obsidian-status-danger)]'
);

// Fix 7: Loading spinner
content = content.replace(
  /text-cyan-600 dark:text-cyan-400/g,
  'text-[var(--cyan-500)] dark:text-[var(--cyan-500)]'
);

// Fix 8: Quick jump links backgrounds
content = content.replace(
  /bg-cyan-950\/20 text-cyan-700 dark:text-cyan-300 hover:bg-cyan-600 hover:text-white/g,
  'bg-[var(--cyan-600)]/20 text-[var(--text-primary)] dark:text-[var(--text-primary)] hover:bg-[var(--cyan-500)] hover:text-[var(--text-inverse)]'
);

content = content.replace(
  /bg-amber-950\/20 text-amber-700 dark:text-amber-300 hover:bg-amber-600 hover:text-white/g,
  'bg-[var(--amber-500)]/20 text-[var(--text-primary)] dark:text-[var(--text-primary)] hover:bg-[var(--amber-500)] hover:text-[var(--text-inverse)]'
);

content = content.replace(
  /bg-purple-950\/20 text-purple-700 dark:text-purple-300 hover:bg-purple-600 hover:text-white/g,
  'bg-[var(--text-primary)]/20 text-[var(--text-primary)] dark:text-[var(--text-primary)] hover:bg-[var(--text-primary)] hover:text-[var(--text-inverse)]'
);

fs.writeFileSync(path, content, 'utf8');
console.log('Dashboard fixes applied!');
