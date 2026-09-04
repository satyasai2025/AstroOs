$content = Get-Content 'apps/web/src/components/phalita/PhalitaCanonicalDashboard.tsx' -Raw -Encoding UTF8
$remaining = @()

if ($content -match 'bg-\[#0b1424\]') { $remaining += 'bg-[#0b1424]' }
if ($content -match 'bg-\[#070e1c\]') { $remaining += 'bg-[#070e1c]' }
if ($content -match 'bg-\[#17263c\]') { $remaining += 'bg-[#17263c]' }
if ($content -match 'bg-cyan-50 dark:bg-cyan-950') { $remaining += 'Recalculate btn' }
if ($content -match 'bg-emerald-50 dark:bg-emerald-950') { $remaining += 'Export btn' }
if ($content -match 'text-cyan-700 dark:text-cyan-300') { $remaining += 'Quick links text' }

Write-Host "Remaining hardcoded colors:"
$remaining | ForEach-Object { Write-Host "  - $_" }
if ($remaining.Count -eq 0) { Write-Host "  All replaced with CSS vars!" }
