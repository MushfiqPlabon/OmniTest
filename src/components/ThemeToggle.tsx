import { Monitor, Moon, Sun } from "@lucide/solid";
import { cycleColorScheme, schemePref } from "@/state/theme";

export function ThemeToggle() {
  const nextLabel = () => {
    const p = schemePref();
    if (p === "light dark") return "Theme: System (click to switch to Light)";
    return p === "light" ? "Theme: Light (click to switch to Dark)" : "Theme: Dark (click to follow System)";
  };

  return (
    <button
      type="button"
      title={nextLabel()}
      aria-label={nextLabel()}
      class="glass-btn inline-flex items-center gap-1.5 rounded-full border border-edge bg-surface/80 px-3 py-1.5 text-xs font-medium text-ink"
      onClick={() => cycleColorScheme()}
    >
      <span class="theme-toggle-opt theme-opt-system items-center gap-1.5">
        <Monitor class="h-3.5 w-3.5 text-brand" />
        <span class="hidden sm:inline">System</span>
      </span>
      <span class="theme-toggle-opt theme-opt-light items-center gap-1.5">
        <Sun class="h-3.5 w-3.5 text-accent" />
        <span class="hidden sm:inline">Light</span>
      </span>
      <span class="theme-toggle-opt theme-opt-dark items-center gap-1.5">
        <Moon class="h-3.5 w-3.5 text-brand" />
        <span class="hidden sm:inline">Dark</span>
      </span>
    </button>
  );
}
