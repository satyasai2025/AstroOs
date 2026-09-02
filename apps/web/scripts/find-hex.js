const fs = require('fs');
const content = fs.readFileSync('apps/web/src/components/phalita/PhalitaCanonicalDashboard.tsx', 'utf8');

const critical = [
  'bg-[#0b1424]', 'bg-[#070e1c]', 'bg-[#17263c]',
  'bg-cyan-500', 'bg-amber-500', 'bg-emerald-500', 'bg-indigo-500', 'bg-purple-500',
  'text-cyan-600', 'text-cyan-700', 'text-cyan-800',
  'text-amber-600', 'text-emerald-600', 'text-indigo-600',
  'border-cyan-500', 'border-amber-500', 'border-emerald-500',
  'bg-cyan-50', 'bg-emerald-50', 'bg-amber-50'
];

console.log('Checking for critical hardcoded hex colors...\n');
let found = 0;
for (const c of critical) {
  const idx = content.indexOf(c);
  if (idx !== -1) {
    const lineNum = content.substring(0, idx).split('\n').length;
    console.log(`FOUND: "${c}" at line ${lineNum}`);
    found++;
  }
}
console.log(`\n${found} critical patterns still present.`);
