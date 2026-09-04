const fs = require('fs');
const globals = fs.readFileSync('src/app/globals.css', 'utf8');
const dashboard = fs.readFileSync('src/components/phalita/PhalitaCanonicalDashboard.tsx', 'utf8');

// Extract CSS variables used in the dashboard
const usedVars = dashboard.match(/var\(--[\w-]+\)/g) || [];
const uniqueVars = [...new Set(usedVars)];
console.log('CSS variables used in dashboard:', uniqueVars.length);
console.log('');

// Check which ones exist in globals.css
let missing = [];
for (const v of uniqueVars) {
  const varName = v.replace(/var\((--[\w-]+)\)/, '$1');
  if (!globals.includes(`--${varName.split('-').slice(1).join('-')}`) && !globals.includes(`:${varName}:`)) {
    missing.push(v);
  }
}
console.log('Variables that need to be added to globals.css:');
if (missing.length === 0) {
  console.log('  All variables exist!');
} else {
  missing.forEach(v => console.log(`  - ${v}`));
}
