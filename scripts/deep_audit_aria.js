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
const allAriaAttrs = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  const regex = /(aria-[a-z]+)=([^\s>]+)/gi;
  let match;
  while ((match = regex.exec(content)) !== null) {
    const lines = content.substring(0, match.index).split('\n');
    allAriaAttrs.push({
      file: path.relative(process.cwd(), file),
      line: lines.length,
      attr: match[1],
      val: match[2]
    });
  }
}

console.log(`Auditing all ${allAriaAttrs.length} ARIA attributes in codebase...`);
allAriaAttrs.forEach(a => {
  // Check suspicious values: empty strings, unboolean expressions for boolean attributes, etc.
  if (a.val === '""' || a.val === "''" || a.val === '{""}') {
    console.log(`⚠️ Empty ARIA attribute: ${a.file}:${a.line} -> ${a.attr}=${a.val}`);
  }
  if (['aria-expanded', 'aria-selected', 'aria-hidden', 'aria-disabled', 'aria-checked'].includes(a.attr.toLowerCase())) {
    // If it's not true/false/boolean
    if (!a.val.includes('true') && !a.val.includes('false') && !a.val.includes('!') && !a.val.includes('===') && !a.val.includes('?') && !a.val.includes('Boolean')) {
      console.log(`ℹ️ Check Boolean ARIA: ${a.file}:${a.line} -> ${a.attr}=${a.val}`);
    }
  }
});
