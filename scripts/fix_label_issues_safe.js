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

  // Match full opening tags for input or textarea safely across single or multi-line
  // <(input|textarea)\b([\s\S]*?)(\/?>)
  const tagRegex = /<(input|textarea)\b([\s\S]*?)(\/?>)/gi;

  content = content.replace(tagRegex, (fullMatch, tag, attrs, closing) => {
    // Skip hidden/button/submit/reset/image
    if (/type=["'](hidden|button|submit|reset|image)["']/i.test(attrs)) {
      return fullMatch;
    }

    // Skip if already has aria-label, aria-labelledby, or title
    if (/aria-label=/i.test(attrs) || /aria-labelledby=/i.test(attrs) || /title=/i.test(attrs)) {
      return fullMatch;
    }

    // Determine label text
    let labelText = '';
    const placeholderMatch = attrs.match(/placeholder=["']([^"']+)["']/i);
    const nameMatch = attrs.match(/name=["']([^"']+)["']/i);
    const idMatch = attrs.match(/id=["']([^"']+)["']/i);
    const typeMatch = attrs.match(/type=["']([^"']+)["']/i);

    if (placeholderMatch) {
      labelText = placeholderMatch[1];
    } else if (nameMatch) {
      labelText = nameMatch[1];
    } else if (idMatch) {
      labelText = idMatch[1];
    } else if (typeMatch) {
      labelText = `${typeMatch[1]} input`;
    } else {
      labelText = `${tag} input`;
    }

    // Sanitize label text for JSX string literal
    labelText = labelText.replace(/["'\\]/g, '').trim() || `${tag} input`;

    fixedCount++;
    // Safely insert aria-label immediately after `<tag `
    return `<${tag} aria-label="${labelText}" ${attrs}${closing}`;
  });

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Added aria-label in: ${path.relative(process.cwd(), file)}`);
  }
}

console.log(`\nUpdated ${fixedCount} inputs/textareas safely with aria-label attributes!`);
