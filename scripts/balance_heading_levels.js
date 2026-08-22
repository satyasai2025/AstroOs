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
let totalAdjusted = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // Convert h3 to h2 when preceded by h1 (and no h2 exists between)
  const headings = [];
  const regex = /<h([1-6])\b/gi;
  let match;
  let hasH1 = false;
  let hasH2 = false;

  const lines = content.split('\n');
  let inH1 = false;

  for (let i = 0; i < lines.length; i++) {
    if (/<h1\b/i.test(lines[i])) {
      hasH1 = true;
      hasH2 = false;
    } else if (/<h2\b/i.test(lines[i])) {
      hasH2 = true;
    } else if (hasH1 && !hasH2 && /<h3\b/i.test(lines[i])) {
      lines[i] = lines[i].replace(/<h3\b/gi, '<h2').replace(/<\/h3>/gi, '</h2>');
    }
  }

  const updatedContent = lines.join('\n');
  if (updatedContent !== original) {
    fs.writeFileSync(file, updatedContent, 'utf8');
    console.log(`Resolved h1->h3 skips in: ${path.relative(process.cwd(), file)}`);
    totalAdjusted++;
  }
}

console.log(`\nResolved heading skips in ${totalAdjusted} files!`);
