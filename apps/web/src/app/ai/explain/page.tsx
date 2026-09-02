import { redirect } from "next/navigation";

/**
 * Legacy AI Explain Prototype Page
 * Deprecated in favor of the canonical Phalita MoE Consultation system (/phalita).
 */
export default function AiExplainPage() {
  redirect("/phalita");
}
