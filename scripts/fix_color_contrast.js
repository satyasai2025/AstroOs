const fs = require('fs');
const path = require('path');

function getAllFiles(dir, exts = ['.tsx', '.jsx', '.css']) {
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
let totalReplacements = 0;

const classReplacements = [
  // Low contrast tailwind classes on dark backgrounds
  { from: /\btext-slate-500\b/g, to: 'text-slate-400' },
  { from: /\btext-zinc-500\b/g, to: 'text-zinc-400' },
  { from: /\btext-gray-500\b/g, to: 'text-gray-400' },
  { from: /\btext-stone-500\b/g, to: 'text-stone-400' },
  { from: /\btext-neutral-500\b/g, to: 'text-neutral-400' },
  
  // Extremely low opacity text
  { from: /\btext-white\/30\b/g, to: 'text-white/60' },
  { from: /\btext-white\/40\b/g, to: 'text-white/70' },
  { from: /\btext-white\/50\b/g, to: 'text-white/75' },
  { from: /\btext-white\/20\b/g, to: 'text-white/50' },
  
  // Extremely dark text classes in dark components
  { from: /\btext-slate-600\b(?!\s*dark:)/g, to: 'text-slate-400' },
  { from: /\btext-zinc-600\b(?!\s*dark:)/g, to: 'text-zinc-400' },
];

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  for (const { from, to } of classReplacements) {
    content = content.replace(from, to);
  }

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    totalReplacements++;
    console.log(`Updated contrast in: ${path.relative(process.cwd(), file)}`);
  }
}

console.log(`\nUpdated ${totalReplacements} files for WCAG 2.1 AA color contrast!`);
