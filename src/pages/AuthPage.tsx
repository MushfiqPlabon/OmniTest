import { createSignal, Show } from "solid-js";
import { AuthHero } from "@/components/auth/AuthHero";
import { ErrorBanner } from "@/components/States";
import { useAuth } from "@/state/auth";

const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3.5 py-2.5 text-sm text-ink";

export function AuthPage() {
  const auth = useAuth();
  const [mode, setMode] = createSignal<"login" | "register">("login");
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [fullName, setFullName] = createSignal("");
  const [pending, setPending] = createSignal(false);
  const [errorMsg, setErrorMsg] = createSignal<string | null>(null);

  const submitForm = async (e: SubmitEvent) => {
    e.preventDefault();
    setPending(true);
    setErrorMsg(null);
    try {
      if (mode() === "login") await auth.login(email().trim(), password());
      else await auth.register(email().trim(), password(), fullName().trim());
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setPending(false);
    }
  };

  const runDemo = async (role: "student" | "admin") => {
    setPending(true);
    setErrorMsg(null);
    try {
      await auth.loginDemo(role);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Demo login failed.");
    } finally {
      setPending(false);
    }
  };

  return (
    <div class="mx-auto grid max-w-4xl gap-8 py-6 lg:grid-cols-[1.15fr_1fr] lg:items-center">
      <AuthHero pending={pending()} onDemo={runDemo} />

      <section class="glass-surface rounded-3xl p-6 sm:p-7">
        <div class="mb-5 grid grid-cols-2 rounded-xl border border-edge bg-canvas p-1" role="tablist">
          {(["login", "register"] as const).map((tab) => (
            <button
              type="button"
              role="tab"
              aria-selected={mode() === tab ? "true" : "false"}
              class={[
                "rounded-lg py-2 text-sm font-medium transition-colors",
                mode() === tab ? "bg-surface text-ink shadow-xs" : "text-muted hover:text-ink",
              ]}
              onClick={() => {
                setMode(tab);
                setErrorMsg(null);
              }}
            >
              {tab === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        <Show when={errorMsg()}>
          {(msg) => (
            <div class="mb-4">
              <ErrorBanner error={msg()} />
            </div>
          )}
        </Show>

        <form onSubmit={submitForm} class="space-y-4">
          <Show when={mode() === "register"}>
            <label class="block space-y-1 text-sm">
              <span class="font-medium text-ink">Full name</span>
              <input
                type="text"
                required
                minlength={2}
                value={fullName()}
                onInput={(e) => setFullName(e.currentTarget.value)}
                placeholder="Rahim Ahmed"
                class={INPUT_CLS}
              />
            </label>
          </Show>

          <label class="block space-y-1 text-sm">
            <span class="font-medium text-ink">Email</span>
            <input
              type="email"
              required
              autocomplete="email"
              value={email()}
              onInput={(e) => setEmail(e.currentTarget.value)}
              placeholder="student@omnitest.com"
              class={INPUT_CLS}
            />
          </label>

          <label class="block space-y-1 text-sm">
            <span class="font-medium text-ink">Password</span>
            <input
              type="password"
              required
              minlength={6}
              autocomplete={mode() === "login" ? "current-password" : "new-password"}
              value={password()}
              onInput={(e) => setPassword(e.currentTarget.value)}
              placeholder="At least 6 characters"
              class={INPUT_CLS}
            />
          </label>

          <button
            type="submit"
            disabled={pending()}
            class="glass-btn w-full rounded-xl bg-brand py-2.5 text-sm font-semibold text-brand-ink disabled:opacity-50"
          >
            {pending() ? "Please wait..." : mode() === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
      </section>
    </div>
  );
}
