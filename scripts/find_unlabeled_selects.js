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
const selectsWithoutLabels = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match all <select ... > tags
  const regex = /<select\b([^>]*)>/g;
  let match;

  while ((match = regex.exec(content)) !== null) {
    const attrs = match[1];
    const lines = content.substring(0, match.index).split('\n');
    const lineNum = lines.length;

    const hasAriaLabel = /aria-label\s*=/i.test(attrs);
    const hasAriaLabelledBy = /aria-labelledby\s*=/i.test(attrs);
    const hasTitle = /title\s*=/i.test(attrs);
    const hasId = /id\s*=\s*["'{]([^"'{}]+)["'}]/i.exec(attrs);

    let hasAssociatedLabel = false;
    if (hasId) {
      const idVal = hasId[1];
      const labelRegex = new RegExp(`<label[^>]*htmlFor=["'{]${idVal}["'}]`, 'i');
      hasAssociatedLabel = labelRegex.test(content);
    }

    if (!hasAriaLabel && !hasAriaLabelledBy && !hasTitle && !hasAssociatedLabel) {
      selectsWithoutLabels.push({
        file: path.relative(process.cwd(), file),
        line: lineNum,
        snippet: match[0].replace(/\s+/g, ' ').slice(0, 140)
      });
    }
  }
}

console.log(`Found ${selectsWithoutLabels.length} <select> elements missing accessible name:`);
selectsWithoutLabels.forEach(s => {
  console.log(`- ${s.file}:${s.line} -> ${s.snippet}`);
});
