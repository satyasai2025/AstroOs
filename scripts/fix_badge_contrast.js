const fs = require('fs');
const path = require('path');

function getAllFiles(dir, exts = ['.tsx', '.jsx']) {
  let files = [];
  for (const item of fs.readdirSync(dir)) {
    const full = path.join(dir, item);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (item !== 'node_modules' && item !== '.next' && item !== '.git') {
        files = files.concat(getAllFiles(full, exts));
      }
    } else if (exts.some(ext => item.endsWith(ext))) {
      files.push(full);
    }
  }
  return files;
}

const files = getAllFiles(path.resolve(__dirname, '../apps/web/src'));
let updatedCount = 0;

const replacements = [
  // 1. Light Mode text colors for amber/cyan
  { from: /\btext-amber-600\b/g, to: 'text-amber-700' },
  { from: /\btext-amber-500\b/g, to: 'text-amber-700' },
  { from: /\btext-cyan-600\b/g, to: 'text-cyan-700' },
  { from: /\btext-cyan-500\b/g, to: 'text-cyan-700' },
  { from: /\btext-indigo-400\b/g, to: 'text-indigo-600' },

  // 2. High-contrast avatar backgrounds (10b981 -> 047857, 14b8a6 -> 0f766e, 6366f1 -> 4f46e5)
  { from: /background:\s*(["'])?rgb\(16,\s*185,\s*129\)\1/gi, to: 'background: #047857' },
  { from: /background:\s*(["'])?rgb\(20,\s*184,\s*166\)\1/gi, to: 'background: #0f766e' },
  { from: /background:\s*(["'])?rgb\(99,\s*102,\s*241\)\1/gi, to: 'background: #4f46e5' },

  // 3. Status badge text colors (rgb 52, 211, 153 -> 047857, rgb 248, 113, 113 -> be123c, rgb 251, 191, 36 -> b45309)
  { from: /color:\s*(["'])?rgb\(52,\s*211,\s*153\)\1/gi, to: 'color: #047857' },
  { from: /color:\s*(["'])?rgb\(248,\s*113,\s*113\)\1/gi, to: 'color: #be123c' },
  { from: /color:\s*(["'])?rgb\(251,\s*191,\s*36\)\1/gi, to: 'color: #b45309' },

  // 4. Cyan button badge high contrast
  { from: /\bbg-cyan-500\/20\s+border-cyan-400\s+text-cyan-300\b/g, to: 'bg-cyan-100 dark:bg-cyan-900/50 border-cyan-500 text-cyan-800 dark:text-cyan-200' },
  { from: /\bbg-cyan-400\/10\s+text-cyan-300\b/g, to: 'bg-cyan-100 dark:bg-cyan-900/50 text-cyan-800 dark:text-cyan-200' },
];

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  for (const { from, to } of replacements) {
    content = content.replace(from, to);
  }

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Updated high-contrast status colors in: ${path.relative(process.cwd(), file)}`);
    updatedCount++;
  }
}

console.log(`\nUpdated ${updatedCount} files for high-contrast status badges!`);
