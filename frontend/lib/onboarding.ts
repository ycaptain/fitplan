import type { Goal, SplitName } from "./types";

export interface OnboardingPrefs {
  goal: Goal;
  split: SplitName;
  sessions_per_week: number;
  preferred_time_of_day: "morning" | "evening" | "any";
}

const STORAGE_KEY = "fitplan.onboarding";

export const DEFAULT_PREFS: OnboardingPrefs = {
  goal: "general",
  split: "ppl",
  sessions_per_week: 4,
  preferred_time_of_day: "any",
};

export function savePrefs(prefs: OnboardingPrefs) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

export function loadPrefs(): OnboardingPrefs | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<OnboardingPrefs>;
    return { ...DEFAULT_PREFS, ...parsed };
  } catch {
    return null;
  }
}
