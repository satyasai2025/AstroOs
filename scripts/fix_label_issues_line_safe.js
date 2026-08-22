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
  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n');
  let modified = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Look for <input or <textarea line
    const match = line.match(/<(input|textarea)\b([^>]*)/i);
    if (match) {
      const tag = match[1];
      const tagLineAttrs = match[2];

      // Check context in the whole tag (look ahead until > or />)
      let tagFullContext = '';
      for (let j = i; j < Math.min(lines.length, i + 15); j++) {
        tagFullContext += lines[j] + ' ';
        if (lines[j].includes('>')) break;
      }

      // Skip hidden/button/submit/reset/image
      if (/type=["'](hidden|button|submit|reset|image)["']/i.test(tagFullContext)) {
        continue;
      }

      // Skip if already has aria-label, aria-labelledby, or title
      if (/aria-label=/i.test(tagFullContext) || /aria-labelledby=/i.test(tagFullContext) || /title=/i.test(tagFullContext)) {
        continue;
      }

      // Extract label text from full tag context
      let labelText = '';
      const placeholderMatch = tagFullContext.match(/placeholder=["']([^"']+)["']/i);
      const nameMatch = tagFullContext.match(/name=["']([^"']+)["']/i);
      const idMatch = tagFullContext.match(/id=["']([^"']+)["']/i);
      const typeMatch = tagFullContext.match(/type=["']([^"']+)["']/i);

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

      labelText = labelText.replace(/["'\\]/g, '').trim() || `${tag} input`;

      // Modify ONLY line i by inserting aria-label right after <tag
      lines[i] = line.replace(new RegExp(`<${tag}\\b`, 'i'), `<${tag} aria-label="${labelText}"`);
      modified = true;
      fixedCount++;
    }
  }

  if (modified) {
    fs.writeFileSync(file, lines.join('\n'), 'utf8');
    console.log(`Safely updated: ${path.relative(process.cwd(), file)}`);
  }
}

console.log(`\nSafely updated ${fixedCount} input/textarea elements!`);
