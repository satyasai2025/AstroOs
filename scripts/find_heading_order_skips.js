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
const headingSkips = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match all <h1 ...>, <h2 ...>, <h3 ...>, <h4 ...>, <h5 ...>, <h6 ...>
  const headingRegex = /<h([1-6])\b([^>]*)>([\s\S]*?)<\/h\1>/gi;
  let match;
  let lastLevel = 0;

  while ((match = headingRegex.exec(content)) !== null) {
    const currentLevel = parseInt(match[1], 10);
    if (lastLevel > 0 && currentLevel > lastLevel + 1) {
      const lines = content.substring(0, match.index).split('\n');
      headingSkips.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        from: `h${lastLevel}`,
        to: `h${currentLevel}`,
        snippet: match[0].replace(/\s+/g, ' ').substring(0, 80)
      });
    }
    lastLevel = currentLevel;
  }
}

console.log(`Found ${headingSkips.length} heading-order skips:\n`);
headingSkips.forEach(v => {
  console.log(`- ${v.file}:${v.line} -> Skips from <${v.from}> to <${v.to}>`);
  console.log(`   ${v.snippet}\n`);
});
