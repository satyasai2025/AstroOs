import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "House Dependency 2",
};

export default function HouseDependency2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}