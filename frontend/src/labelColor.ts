export function labelClass(label: string): string {
  if (label === "Humano") return "label--human";
  if (label === "Indicios de IA") return "label--hints";
  return "label--ai";
}
