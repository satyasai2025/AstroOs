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
const scrollableContainers = [];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match classNames with overflow-(x-|y-)?(auto|scroll) or style={{ ...overflow... }}
  const regex = /<([a-zA-Z0-9_]+)\b([^>]*?(?:className=["'][^"']*overflow-(?:x-|y-)?(?:auto|scroll)[^"']*["']|style=\{\{[^}]*overflow[^}]*\}\})[^>]*)>/g;
  let match;

  while ((match = regex.exec(content)) !== null) {
    const tag = match[1];
    const attrs = match[2];

    // Check if it already has tabIndex or tabindex
    const hasTabIndex = /tabIndex|tabindex/i.test(attrs);

    if (!hasTabIndex) {
      const lines = content.substring(0, match.index).split('\n');
      scrollableContainers.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        tag,
        attrs: attrs.replace(/\s+/g, ' ').slice(0, 120)
      });
    }
  }
}

console.log(`Found ${scrollableContainers.length} scrollable containers missing tabIndex:`);
scrollableContainers.forEach(c => {
  console.log(`- ${c.file}:${c.line} <${c.tag} ${c.attrs}...>`);
});
