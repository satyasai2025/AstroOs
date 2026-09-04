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

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');

  // Search for <Link ... > ... <button ... >
  const linkWithButton = /<(Link|a)\b[^>]*>[\s\S]*?<button\b/gi;
  let m;
  while ((m = linkWithButton.exec(content)) !== null) {
    const lines = content.substring(0, m.index).split('\n');
    console.log(`[Link containing Button] ${path.relative(process.cwd(), file)}:${lines.length}`);
    console.log(`   ${m[0].slice(0, 150).replace(/\s+/g, ' ')}...\n`);
  }

  // Search for <button ... > ... <(Link|a)\b
  const buttonWithLink = /<button\b[^>]*>[\s\S]*?<(Link|a)\b/gi;
  while ((m = buttonWithLink.exec(content)) !== null) {
    const lines = content.substring(0, m.index).split('\n');
    console.log(`[Button containing Link] ${path.relative(process.cwd(), file)}:${lines.length}`);
    console.log(`   ${m[0].slice(0, 150).replace(/\s+/g, ' ')}...\n`);
  }
}
