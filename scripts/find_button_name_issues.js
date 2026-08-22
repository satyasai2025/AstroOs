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
const buttonViolations = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match <button ...> ... </button>
  const buttonRegex = /<button\b([^>]*)>([\s\S]*?)<\/button>/gi;
  let match;

  while ((match = buttonRegex.exec(content)) !== null) {
    const attrs = match[1];
    const innerHTML = match[2].trim();

    const hasAriaLabel = /aria-label=/i.test(attrs);
    const hasAriaLabelledBy = /aria-labelledby=/i.test(attrs);
    const hasTitle = /title=/i.test(attrs);

    // Check if innerHTML contains any visible text (strip SVG, HTML tags)
    const textContent = innerHTML.replace(/<svg[\s\S]*?<\/svg>/gi, '').replace(/<[^>]+>/g, '').trim();

    if (!hasAriaLabel && !hasAriaLabelledBy && !hasTitle && !textContent) {
      const lines = content.substring(0, match.index).split('\n');
      buttonViolations.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        snippet: match[0].replace(/\s+/g, ' ').substring(0, 100)
      });
    }
  }
}

console.log(`Found ${buttonViolations.length} button-name violations:\n`);
buttonViolations.slice(0, 30).forEach(v => {
  console.log(`- ${v.file}:${v.line} -> ${v.snippet}`);
});
