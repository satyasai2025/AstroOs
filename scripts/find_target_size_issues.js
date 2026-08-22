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
const smallTargets = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match buttons or links with explicit small dimensions
  const regex = /<(button|a)\b([^>]*)>/gi;
  let match;

  while ((match = regex.exec(content)) !== null) {
    const attrs = match[2];
    const isSmallClass = /\b(h-3|w-3|h-3\.5|w-3\.5|h-4|w-4|h-5|w-5)\b/.test(attrs);
    const isSmallStyle = /height:\s*(12|14|16|18|20)px|width:\s*(12|14|16|18|20)px/.test(attrs);

    if (isSmallClass || isSmallStyle) {
      const lines = content.substring(0, match.index).split('\n');
      smallTargets.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        snippet: match[0].replace(/\s+/g, ' ').substring(0, 100)
      });
    }
  }
}

console.log(`Found ${smallTargets.length} small target-size candidates:\n`);
smallTargets.forEach(v => {
  console.log(`- ${v.file}:${v.line} -> ${v.snippet}`);
});
