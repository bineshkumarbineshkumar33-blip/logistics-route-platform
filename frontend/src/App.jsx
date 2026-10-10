import { useState } from "react";
import MapView from "./components/MapView";
import Sidebar from "./components/Sidebar";
import { api, useLiveState } from "./useLiveState";

export default function App() {
  const { state, connected } = useLiveState();
  const [armed, setArmed] = useState(false);
  const [form, setForm] = useState({ name: "", weight_kg: 3, priority: 1 });

  if (!state) {
    return (
      <div className="grid h-full place-items-center p-6 text-center">
        <div>
          <h1 className="font-display text-2xl font-bold">Waiting for the backend</h1>
          <p className="mt-2 text-ink/70">Start FastAPI on port 8000, then this page connects on its own.</p>
        </div>
      </div>
    );
  }

  const place = async (lat, lng) => {
    await api.addOrder({ name: form.name.trim() || `Order #${state.orders.length + 1}`, lat, lng, weight_kg: Number(form.weight_kg) || 3, priority: Number(form.priority) });
    setArmed(false);
    setForm({ ...form, name: "" });
  };

  return (
    <div className="flex h-full flex-col md:flex-row">
      <Sidebar state={state} connected={connected} armed={armed} setArmed={setArmed} form={form} setForm={setForm} />
      <main className="min-h-[50vh] flex-1">
        <MapView state={state} armed={armed} onPlace={place} onStatus={api.setStatus} />
      </main>
    </div>
  );
}
