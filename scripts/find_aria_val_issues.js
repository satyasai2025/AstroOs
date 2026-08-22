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
const ariaIssues = [];

const validValues = {
  'aria-haspopup': ['true', 'false', 'menu', 'listbox', 'tree', 'grid', 'dialog'],
  'aria-expanded': ['true', 'false'],
  'aria-hidden': ['true', 'false'],
  'aria-selected': ['true', 'false'],
  'aria-checked': ['true', 'false', 'mixed'],
  'aria-disabled': ['true', 'false'],
  'aria-current': ['true', 'false', 'page', 'step', 'location', 'date', 'time'],
  'aria-invalid': ['true', 'false', 'grammar', 'spelling'],
  'aria-live': ['off', 'polite', 'assertive'],
  'aria-autocomplete': ['inline', 'list', 'both', 'none'],
  'aria-orientation': ['horizontal', 'vertical'],
  'aria-sort': ['ascending', 'descending', 'none', 'other']
};

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Match all aria-[a-z]+=["'{]([^"'{}]+)["'}] or aria-[a-z]+=\{([^}]+)\}
  const regex = /(aria-[a-z]+)=["']([^"']*)["']/gi;
  let match;
  while ((match = regex.exec(content)) !== null) {
    const attr = match[1].toLowerCase();
    const val = match[2];

    if (validValues[attr] && !validValues[attr].includes(val)) {
      const lines = content.substring(0, match.index).split('\n');
      ariaIssues.push({
        file: path.relative(process.cwd(), file),
        line: lines.length,
        attr,
        val,
        snippet: match[0]
      });
    }
  }

  // Also check expression values like aria-expanded={...} or aria-selected={...}
  const exprRegex = /(aria-[a-z]+)=\{([^}]+)\}/gi;
  while ((match = exprRegex.exec(content)) !== null) {
    const attr = match[1].toLowerCase();
    const expr = match[2].trim();

    // Check for string literals inside JSX expression: aria-haspopup={"..."}
    if (expr.startsWith('"') || expr.startsWith("'")) {
      const strVal = expr.slice(1, -1);
      if (validValues[attr] && !validValues[attr].includes(strVal)) {
        const lines = content.substring(0, match.index).split('\n');
        ariaIssues.push({
          file: path.relative(process.cwd(), file),
          line: lines.length,
          attr,
          val: strVal,
          snippet: match[0]
        });
      }
    }
  }
}

console.log(`Found ${ariaIssues.length} invalid aria attribute values:`);
ariaIssues.forEach(iss => {
  console.log(`- ${iss.file}:${iss.line} -> ${iss.attr}="${iss.val}" (valid: ${validValues[iss.attr].join(', ')})`);
});
