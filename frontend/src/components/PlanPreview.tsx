import { StatusBadge } from "./StatusBadge";

export function PlanPreview({ plan }: { plan: Record<string, unknown> }) {
  const gates = (plan.approval_gates as Array<{ label: string; detail: string }>) || [];
  return (
    <section aria-label="Plan preview" className="rounded border border-zinc-800 p-4" data-testid="plan-preview">
      <h3 className="font-semibold">Plan preview</h3>
      <dl className="mt-2 grid gap-1 text-sm">
        <div><dt className="inline text-zinc-500">Classification: </dt><dd className="inline">{String(plan.classification)}</dd></div>
        <div><dt className="inline text-zinc-500">Agent: </dt><dd className="inline mono">{String(plan.selected_agent)}</dd></div>
        <div><dt className="inline text-zinc-500">Fallbacks: </dt><dd className="inline mono">{((plan.fallback_agents as string[]) || []).join(", ")}</dd></div>
        <div><dt className="inline text-zinc-500">Provider/Model: </dt><dd className="inline mono">{String(plan.provider)} / {String(plan.model)}</dd></div>
        <div><dt className="inline text-zinc-500">Environment: </dt><dd className="inline mono">{String(plan.environment)}</dd></div>
        <div><dt className="inline text-zinc-500">Verification: </dt><dd className="inline">{String(plan.verification_strategy)}</dd></div>
        <div><dt className="inline text-zinc-500">Budget: </dt><dd className="inline mono">{String(plan.budget)}</dd></div>
      </dl>
      <div className="mt-2 flex flex-wrap gap-2">
        {gates.map((g, i) => (
          <span key={i} className="mono rounded border border-zinc-700 px-2 py-0.5 text-xs" title={g.detail}>
            {g.label}
          </span>
        ))}
      </div>
      <p className="mt-2 text-xs text-zinc-500">No secret values are shown. Paid steps need explicit approval.</p>
    </section>
  );
}
