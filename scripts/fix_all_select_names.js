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

  // Pattern: <label ...>(Label Text)</label>\s*<select (without aria-label)
  // We can add aria-label="Label Text" or id/htmlFor
  const regex = /(<label[^>]*>\s*([A-Za-z0-9\s/&,._\-—()]+?)\s*<\/label>\s*<select\b)(?![^>]*aria-label)([^>]*>)/gi;
  
  content = content.replace(regex, (match, prefix, labelText, suffix) => {
    const cleanLabel = labelText.trim().replace(/"/g, "'");
    if (!cleanLabel) return match;
    fixedCount++;
    return `${prefix} aria-label="${cleanLabel}"${suffix}`;
  });

  // Also standalone selects without aria-label (e.g., toolbar filters)
  // If select has value={...something...} or name={...} or className={...}, give it an aria-label if missing
  const standaloneSelectRegex = /<select\b(?![^>]*aria-label)([^>]*)>/gi;
  content = content.replace(standaloneSelectRegex, (match, attrs) => {
    // Check if it already has aria-label or aria-labelledby or title
    if (/aria-label|aria-labelledby|title/i.test(attrs)) {
      return match;
    }

    // Infer a meaningful name from value or id or name or placeholder
    let inferredName = "Select option";
    const valueMatch = /value=\{([a-zA-Z0-9_$.]+)\}/.exec(attrs);
    const idMatch = /id=["'{]([^"'{}]+)["'}]/.exec(attrs);
    const nameMatch = /name=["'{]([^"'{}]+)["'}]/.exec(attrs);

    if (idMatch) {
      inferredName = idMatch[1].replace(/[-_]/g, ' ');
    } else if (nameMatch) {
      inferredName = nameMatch[1].replace(/[-_]/g, ' ');
    } else if (valueMatch) {
      // e.g. settings.zodiac -> Zodiac, selectedPlanet -> Selected planet
      const valStr = valueMatch[1].split('.').pop();
      inferredName = valStr.replace(/([A-Z])/g, ' $1').toLowerCase().trim();
      inferredName = inferredName.charAt(0).toUpperCase() + inferredName.slice(1);
    }

    fixedCount++;
    return `<select aria-label="${inferredName}"${attrs}>`;
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Updated selects in: ${path.relative(process.cwd(), file)}`);
  }
}

console.log(`\nSuccessfully added aria-label to ${fixedCount} select element(s)!`);
