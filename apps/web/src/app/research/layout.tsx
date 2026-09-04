// Research workspace uses its own NavPanel — skip AppShell (and its auth redirect)
export default function ResearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
