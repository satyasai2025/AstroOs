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
let fixedCount = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // Match <button ...> ... </button>
  const buttonRegex = /<button\b([^>]*)>([\s\S]*?)<\/button>/gi;

  content = content.replace(buttonRegex, (fullMatch, attrs, innerHTML) => {
    const hasAriaLabel = /aria-label=/i.test(attrs);
    const hasAriaLabelledBy = /aria-labelledby=/i.test(attrs);
    const hasTitle = /title=/i.test(attrs);

    // Strip SVG tags and HTML tags to see if text content exists
    const textContent = innerHTML.replace(/<svg[\s\S]*?<\/svg>/gi, '').replace(/<[^>]+>/g, '').trim();

    if (!hasAriaLabel && !hasAriaLabelledBy && !hasTitle && !textContent) {
      fixedCount++;
      // Determine appropriate label from className, onClick, or fallback
      let label = "Action button";
      if (/close|dismiss/i.test(attrs) || /onClose/i.test(attrs)) {
        label = "Close dialog";
      } else if (/star|bookmark|favorite/i.test(attrs)) {
        label = "Bookmark item";
      } else if (/search/i.test(attrs)) {
        label = "Search";
      } else if (/toggle|collapse|expand/i.test(attrs)) {
        label = "Toggle view";
      }

      return `<button ${attrs.trim()} aria-label="${label}">${innerHTML}</button>`;
    }
    return fullMatch;
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Fixed button names in: ${path.relative(process.cwd(), file)}`);
  }
}

console.log(`\nFixed ${fixedCount} icon-only button accessible names!`);
