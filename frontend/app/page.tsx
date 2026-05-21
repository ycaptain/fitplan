import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">FitPlan AI</h1>
      <p className="max-w-xl text-center text-slate-600">
        Adaptive AI workout scheduling assistant. Tell us your goals and
        constraints. We&apos;ll plan your week. Break it, and we&apos;ll fix it.
      </p>
      <div className="flex gap-4">
        <Link
          href="/onboarding"
          className="rounded-md bg-slate-900 px-4 py-2 text-white hover:bg-slate-700"
        >
          Get started
        </Link>
        <Link
          href="/plan"
          className="rounded-md border border-slate-300 px-4 py-2 hover:bg-slate-50"
        >
          View plan
        </Link>
      </div>
    </main>
  );
}
