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
let fixedHeadings = 0;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  let original = content;

  // Fix h1 followed by h4 -> change h4 to h2
  content = content.replace(/(<h1\b[\s\S]*?<\/h1>[\s\S]*?)<h4\b/gi, '$1<h2');
  content = content.replace(/(<h1\b[\s\S]*?<\/h1>[\s\S]*?)<\/h4>/gi, '$1</h2>');

  // Fix h1 followed by h3 -> change h3 to h2 (when no h2 is between)
  // Let's do precise regex replacements for the specific component files
  if (file.includes('charts\\birth\\page.tsx') || file.includes('charts/birth/page.tsx')) {
    content = content.replace(/<h3 className="mb-1\.5 text-xs/g, '<h2 className="mb-1.5 text-xs');
    content = content.replace(/<\/h3>/g, '</h2>');
  } else if (file.includes('charts\\page.tsx') || file.includes('charts/page.tsx')) {
    content = content.replace(/<h4 className="mb-1 text-xs/g, '<h2 className="mb-1 text-xs');
    content = content.replace(/<\/h4>/g, '</h2>');
  } else if (file.includes('knowledge-graph\\page.tsx') || file.includes('knowledge-graph/page.tsx')) {
    content = content.replace(/<h4 className="text-xs font-semibold/g, '<h3 className="text-xs font-semibold');
    content = content.replace(/<\/h4>/g, '</h3>');
  } else if (file.includes('predictions\\page.tsx') || file.includes('predictions/page.tsx')) {
    content = content.replace(/<h3 className="mb-2 text-sm/g, '<h2 className="mb-2 text-sm');
    content = content.replace(/<\/h3>/g, '</h2>');
  } else if (file.includes('BenchmarkLab.tsx')) {
    content = content.replace(/<h5 className="font-semibold text-zinc-300/g, '<h4 className="font-semibold text-zinc-300');
    content = content.replace(/<\/h5>/g, '</h4>');
  } else if (file.includes('TarabalaPanel.tsx')) {
    content = content.replace(/<h4 className="text-xs font-bold text-foreground/g, '<h3 className="text-xs font-bold text-foreground');
    content = content.replace(/<\/h4>/g, '</h3>');
  } else if (file.includes('PredictionConfluenceWorkspace.tsx')) {
    content = content.replace(/<h4 className="text-sm font-bold/g, '<h2 className="text-sm font-bold');
    content = content.replace(/<h4 className="text-xs font-bold/g, '<h3 className="text-xs font-bold');
    content = content.replace(/<\/h4>/g, '</h2>');
  }

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Fixed heading order in: ${path.relative(process.cwd(), file)}`);
    fixedHeadings++;
  }
}

console.log(`\nFixed heading hierarchy in ${fixedHeadings} files!`);
