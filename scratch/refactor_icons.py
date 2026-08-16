"""Refactor component files to use the shared Icon component."""
import re
import sys

BASE = r"c:\Users\rkmau\Downloads\ReplitplusClaude\AstroOS\apps\web\src"

# ========================================================================
# 1. NavPanel.tsx — replace inline NavIcon with shared Icon + fix naming
# ========================================================================
navpanel_path = BASE + r"\components\layout\NavPanel.tsx"
with open(navpanel_path, "r") as f:
    c = f.read()

# Add import
c = c.replace(
    'import { useCallback, useState } from "react";',
    'import { useCallback, useState } from "react";\nimport { Icon, type IconName } from "@/components/ui/Icon";',
)

# Change icon type in NavItem interface
c = c.replace(
    "  icon: string;\n  disabled?: boolean;",
    "  icon: IconName;\n  disabled?: boolean;",
)
# Change icon type in NavModule interface
c = c.replace(
    "  icon: string;\n  color: string;",
    "  icon: IconName;\n  color: string;",
)

# Fix label: "Interactive Kundli" -> "Birth Chart"
c = c.replace(
    'label: "Interactive Kundli"',
    'label: "Birth Chart"',
)

# Replace the entire NavIcon function with a thin wrapper
pattern = r'function NavIcon\(\{ name, className = "" \}: \{ name: string; className\?: string \}\) \{.*?\n\}'
replacement = (
    'function NavIcon({ name, className = "h-4 w-4 flex-shrink-0" }: { name: IconName; className?: string }) {\n'
    '  return <Icon name={name} className={className} />;\n'
    '}'
)
c = re.sub(pattern, replacement, c, flags=re.DOTALL)

with open(navpanel_path, "w") as f:
    f.write(c)

checks_navpanel = [
    ('import added', 'from "@/components/ui/Icon"' in c),
    ('NavIcon replaced', '<Icon name={name} className={className}' in c),
    ('no switch in NavIcon', 'switch (name)' not in c.split('function NavIcon')[1].split('\n\n')[0] if 'function NavIcon' in c else False),
    ('label fixed', 'label: "Birth Chart"' in c),
    ('IconName type', 'icon: IconName;' in c),
]
print("=== NavPanel.tsx ===")
for label, ok in checks_navpanel:
    print(f"  {'PASS' if ok else 'FAIL'}: {label}")

# ========================================================================
# 2. AppShell.tsx — replace inline NavIcon with shared Icon
# ========================================================================
appshell_path = BASE + r"\components\layout\AppShell.tsx"
with open(appshell_path, "r") as f:
    c = f.read()

# Add import
c = c.replace(
    'import { useTheme } from "./ThemeProvider";',
    'import { useTheme } from "./ThemeProvider";\nimport { Icon, type IconName } from "@/components/ui/Icon";',
)

# Change icon type in NavItem interface
c = c.replace(
    "  icon: string;\n  disabled?: boolean;",
    "  icon: IconName;\n  disabled?: boolean;",
)

# Replace the entire NavIcon function with a thin wrapper
pattern = r'export function NavIcon\(\{ name \}: \{ name: string \}\) \{.*?\n\}'
replacement = (
    'export function NavIcon({ name }: { name: IconName }) {\n'
    '  return <Icon name={name} />;\n'
    '}'
)
c = re.sub(pattern, replacement, c, flags=re.DOTALL)

with open(appshell_path, "w") as f:
    f.write(c)

checks_appshell = [
    ('import added', 'from "@/components/ui/Icon"' in c),
    ('NavIcon replaced', '<Icon name={name} />' in c and 'switch (name)' not in c),
    ('IconName type', 'icon: IconName;' in c),
]
print("=== AppShell.tsx ===")
for label, ok in checks_appshell:
    print(f"  {'PASS' if ok else 'FAIL'}: {label}")

# ========================================================================
# 3. AdminSidebar.tsx — replace inline AdminNavIcon with shared Icon (size 18)
# ========================================================================
admin_path = BASE + r"\components\admin\AdminSidebar.tsx"
with open(admin_path, "r") as f:
    c = f.read()

# Add import after usePathname import
c = c.replace(
    'import { usePathname } from "next/navigation";',
    'import { usePathname } from "next/navigation";\nimport { Icon, type IconName } from "@/components/ui/Icon";',
)

# Change icon type in AdminNavItem interface
c = c.replace(
    "  icon: string;\n  badge?: string;",
    "  icon: IconName;\n  badge?: string;",
)

# Replace the entire AdminNavIcon function with a thin wrapper (size=18)
pattern = r'function AdminNavIcon\(\{ name \}: \{ name: string \}\) \{.*?\n\}'
replacement = (
    'function AdminNavIcon({ name }: { name: IconName }) {\n'
    '  return <Icon name={name} size={18} />;\n'
    '}'
)
c = re.sub(pattern, replacement, c, flags=re.DOTALL)

with open(admin_path, "w") as f:
    f.write(c)

checks_admin = [
    ('import added', 'from "@/components/ui/Icon"' in c),
    ('AdminNavIcon replaced', '<Icon name={name} size={18}' in c),
    ('IconName type', 'icon: IconName;' in c),
]
print("=== AdminSidebar.tsx ===")
for label, ok in checks_admin:
    print(f"  {'PASS' if ok else 'FAIL'}: {label}")

# ========================================================================
# 4. ResearchDashboard.tsx — replace inline Icon with shared Icon (size 20)
# ========================================================================
dashboard_path = BASE + r"\components\dashboard\ResearchDashboard.tsx"
with open(dashboard_path, "r") as f:
    c = f.read()

# Add import with alias (file has local function named Icon)
c = c.replace(
    'import { useState } from "react";',
    'import { useState } from "react";\nimport { Icon as SharedIcon, type IconName } from "@/components/ui/Icon";',
)

# Replace the local Icon function with a thin wrapper around SharedIcon
pattern = r'function Icon\(\{ name, className = "" \}: \{ name: string; className\?: string \}\) \{.*?\n\}'
replacement = (
    'function Icon({ name, className = "" }: { name: IconName; className?: string }) {\n'
    '  return <SharedIcon name={name} size={20} className={className} />;\n'
    '}'
)
c = re.sub(pattern, replacement, c, flags=re.DOTALL)

with open(dashboard_path, "w") as f:
    f.write(c)

checks_dash = [
    ('import added', 'from "@/components/ui/Icon"' in c),
    ('Icon wrapper replaced', '<SharedIcon name={name} size={20}' in c),
    ('no switch in Icon', 'switch (name)' not in c.split('function Icon')[1].split('\n\n')[0] if 'function Icon' in c else False),
]
print("=== ResearchDashboard.tsx ===")
for label, ok in checks_dash:
    print(f"  {'PASS' if ok else 'FAIL'}: {label}")

# ========================================================================
# 5. charts/page.tsx — fix label "Chart View" -> "Birth Chart"
# ========================================================================
charts_path = BASE + r"\app\(main)\charts\page.tsx"
with open(charts_path, "r") as f:
    c = f.read()

c = c.replace(
    '{ key: "chart" as ViewMode, label: "Chart View" }',
    '{ key: "chart" as ViewMode, label: "Birth Chart" }',
)

with open(charts_path, "w") as f:
    f.write(c)

print("=== charts/page.tsx ===")
print(f"  {'PASS' if 'label: \"Birth Chart\"' in c else 'FAIL'}: label fixed")
