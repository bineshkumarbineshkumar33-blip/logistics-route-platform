import { useState } from "react";
import { api } from "../useLiveState";

function Stat({ value, label }) {
  return (
    <div>
      <div className="font-display text-2xl font-bold leading-none">{value}</div>
      <div className="mt-1 text-xs text-ink/60">{label}</div>
    </div>
  );
}

function AgentCard({ r }) {
  const pct = Math.min(100, (r.load_kg / r.capacity_kg) * 100);
  return (
    <section className="rounded-lg border border-line bg-white" style={{ borderLeft: `6px solid ${r.color}` }}>
      <header className="flex items-baseline justify-between px-3 pt-3">
        <h3 className="font-display text-lg font-bold">{r.name}</h3>
        <span className="text-sm text-ink/70">{r.distance_km} km · {Math.round(r.eta_min)} min</span>
      </header>
      <div className="px-3 pt-2">
        <div className="h-1.5 overflow-hidden rounded-full bg-mist"><div className="h-full" style={{ width: `${pct}%`, background: r.color }} /></div>
        <p className="mt-1 text-xs text-ink/60">{r.load_kg} of {r.capacity_kg} kg loaded · {r.algorithm}</p>
      </div>
      <ol className="mt-2 divide-y divide-line">
        {r.stops.length === 0 && <li className="px-3 py-2 text-sm text-ink/60">No parcels assigned.</li>}
        {r.stops.map((s) => (
          <li key={s.order_id} className="flex items-center gap-2 px-3 py-2 text-sm">
            <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-semibold text-white" style={{ background: r.color }}>{s.seq}</span>
            <span className="min-w-0 flex-1 truncate">{s.name}{s.priority > 1 && <span className="ml-1 text-xs text-ink/50">priority {s.priority}</span>}</span>
            <span className="text-xs text-ink/60">{Math.round(s.eta_min)} min</span>
            <button className="rounded border border-line px-1.5 py-0.5 text-xs hover:bg-mist" onClick={() => api.setStatus(s.order_id, "delayed")}>Delay</button>
            <button className="rounded border border-line px-1.5 py-0.5 text-xs hover:bg-mist" onClick={() => api.setStatus(s.order_id, "delivered")}>Done</button>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default function Sidebar({ state, connected, armed, setArmed, form, setForm }) {
  const { plan, orders } = state;
  const late = orders.filter((o) => o.status === "delayed" || plan.unassigned.includes(o.id));
  const delivered = orders.filter((o) => o.status === "delivered").length;

  return (
    <aside className="flex h-full w-full flex-col gap-3 overflow-y-auto border-r border-line bg-mist p-4 md:w-[400px] md:shrink-0">
      <header className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold">Route Desk</h1>
        <span className="flex items-center gap-2 text-sm">
          <span className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-emerald-500" : "bg-late"}`} />
          {connected ? "Live" : "Reconnecting"}
        </span>
      </header>

      <div className="grid grid-cols-3 gap-3 rounded-lg border border-line bg-white p-3">
        <Stat value={`${plan.total_distance_km} km`} label="Total distance" />
        <Stat value={`${plan.compute_ms} ms`} label="Last re-route" />
        <Stat value={`${delivered}/${orders.length}`} label="Delivered" />
      </div>

      {plan.routes.map((r) => <AgentCard key={r.agent_id} r={r} />)}

      {late.length > 0 && (
        <section className="rounded-lg border border-late/40 bg-white p-3">
          <h3 className="font-display text-lg font-bold text-late">Needs attention</h3>
          <ul className="mt-1 divide-y divide-line text-sm">
            {late.map((o) => (
              <li key={o.id} className="flex items-center justify-between gap-2 py-2">
                <span>{o.name}<span className="ml-1 text-xs text-ink/60">{o.status === "delayed" ? "delayed" : "no room on any vehicle"}</span></span>
                {o.status === "delayed" && <button className="rounded border border-line px-1.5 py-0.5 text-xs hover:bg-mist" onClick={() => api.setStatus(o.id, "pending")}>Resume</button>}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="rounded-lg border border-line bg-white p-3">
        <h3 className="font-display text-lg font-bold">Add an order</h3>
        <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
          <input className="col-span-3 rounded border border-line px-2 py-1.5" placeholder="Customer or area" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} aria-label="Order name" />
          <label className="text-xs text-ink/60">Weight (kg)
            <input type="number" min="1" className="mt-1 w-full rounded border border-line px-2 py-1.5 text-sm text-ink" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} />
          </label>
          <label className="col-span-2 text-xs text-ink/60">Priority
            <select className="mt-1 w-full rounded border border-line px-2 py-1.5 text-sm text-ink" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              <option value={1}>Standard</option><option value={2}>Express</option><option value={3}>Urgent</option>
            </select>
          </label>
        </div>
        <div className="mt-3 flex gap-2">
          <button className={`flex-1 rounded px-3 py-2 text-sm font-medium ${armed ? "bg-ink text-white" : "border border-ink"}`} onClick={() => setArmed(!armed)}>
            {armed ? "Click the map to place it" : "Place on map"}
          </button>
          <button className="rounded border border-line px-3 py-2 text-sm hover:bg-mist" onClick={() => api.randomOrder()}>Random order</button>
        </div>
      </section>

      <button className="self-start text-sm underline" onClick={() => api.reset()}>Reset demo data</button>
    </aside>
  );
}
