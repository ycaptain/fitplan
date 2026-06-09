"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  DEFAULT_PREFS,
  loadPrefs,
  savePrefs,
  type OnboardingPrefs,
} from "@/lib/onboarding";
import type { Goal, SplitName } from "@/lib/types";

const GOALS: Array<{ value: Goal; label: string; hint: string }> = [
  { value: "bulk", label: "Bulk", hint: "Longer sessions, build muscle" },
  { value: "cut", label: "Cut", hint: "Shorter sessions, lose fat" },
  { value: "general", label: "General", hint: "Balanced default" },
];

const SPLITS: Array<{ value: SplitName; label: string }> = [
  { value: "ppl", label: "Push / Pull / Legs" },
  { value: "upper_lower", label: "Upper / Lower" },
  { value: "full_body", label: "Full Body" },
];

const TIMES: Array<{
  value: OnboardingPrefs["preferred_time_of_day"];
  label: string;
}> = [
  { value: "morning", label: "Morning" },
  { value: "evening", label: "Evening" },
  { value: "any", label: "No preference" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [prefs, setPrefs] = useState<OnboardingPrefs>(DEFAULT_PREFS);

  useEffect(() => {
    const saved = loadPrefs();
    if (saved) setPrefs(saved);
  }, []);

  function submit(event: React.FormEvent) {
    event.preventDefault();
    savePrefs(prefs);
    router.push("/plan");
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-2xl font-semibold">Onboarding</h1>
      <p className="mt-2 text-slate-600">
        Tell us how you train. These preferences seed the initial weekly plan.
      </p>

      <form onSubmit={submit} className="mt-6 space-y-6">
        <fieldset>
          <legend className="text-sm font-semibold text-slate-800">Goal</legend>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {GOALS.map((goal) => (
              <label
                key={goal.value}
                className={[
                  "cursor-pointer rounded border p-3 text-sm",
                  prefs.goal === goal.value
                    ? "border-slate-800 bg-slate-100 font-semibold"
                    : "border-slate-300",
                ].join(" ")}
              >
                <input
                  type="radio"
                  name="goal"
                  value={goal.value}
                  checked={prefs.goal === goal.value}
                  onChange={() => setPrefs((p) => ({ ...p, goal: goal.value }))}
                  className="sr-only"
                />
                <span className="block">{goal.label}</span>
                <span className="mt-1 block text-xs font-normal text-slate-500">
                  {goal.hint}
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <label className="block text-sm">
          <span className="font-semibold text-slate-800">Training split</span>
          <select
            value={prefs.split}
            onChange={(e) =>
              setPrefs((p) => ({ ...p, split: e.target.value as SplitName }))
            }
            className="mt-2 w-full rounded border border-slate-300 p-2"
          >
            {SPLITS.map((split) => (
              <option key={split.value} value={split.value}>
                {split.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-semibold text-slate-800">
            Sessions per week: {prefs.sessions_per_week}
          </span>
          <input
            type="range"
            min={2}
            max={6}
            value={prefs.sessions_per_week}
            onChange={(e) =>
              setPrefs((p) => ({
                ...p,
                sessions_per_week: Number(e.target.value),
              }))
            }
            className="mt-2 w-full"
          />
        </label>

        <fieldset>
          <legend className="text-sm font-semibold text-slate-800">
            Preferred time
          </legend>
          <div className="mt-2 flex gap-2">
            {TIMES.map((time) => (
              <label
                key={time.value}
                className={[
                  "cursor-pointer rounded border px-3 py-2 text-sm",
                  prefs.preferred_time_of_day === time.value
                    ? "border-slate-800 bg-slate-100 font-semibold"
                    : "border-slate-300",
                ].join(" ")}
              >
                <input
                  type="radio"
                  name="preferred_time"
                  value={time.value}
                  checked={prefs.preferred_time_of_day === time.value}
                  onChange={() =>
                    setPrefs((p) => ({
                      ...p,
                      preferred_time_of_day: time.value,
                    }))
                  }
                  className="sr-only"
                />
                {time.label}
              </label>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
        >
          Save and open planner
        </button>
      </form>
    </main>
  );
}
