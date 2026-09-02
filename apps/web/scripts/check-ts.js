const fs = require('fs');
const content = fs.readFileSync('ts-errors.txt', 'utf8');
const errors = content.split('\n').filter(line => line.includes('error TS'));
console.log(`Total TypeScript errors: ${errors.length}`);
errors.slice(0, 30).forEach(e => console.log(e));
