import { BarChart3, BookOpen, CheckSquare, MessageSquare, PenTool, Shield } from "@lucide/solid";
import { createMemo, For } from "solid-js";

const STUDENT_NAV = [
  { path: "/chat", label: "AI Tutor", icon: MessageSquare },
  { path: "/quizzes", label: "Quizzes", icon: CheckSquare },
  { path: "/essays", label: "Essays", icon: PenTool },
  { path: "/materials", label: "Study Library", icon: BookOpen },
  { path: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function NavLinks(props: {
  isAdmin: boolean;
  pathname: string;
  mobile?: boolean;
  onNavigate: (href: string) => void;
}) {
  const items = createMemo(() =>
    props.isAdmin ? [{ path: "/admin", label: "Admin", icon: Shield }, ...STUDENT_NAV] : STUDENT_NAV,
  );
  const home = () => (props.isAdmin ? "/admin" : "/chat");
  const isActive = (path: string) => props.pathname === path || (props.pathname === "/" && path === home());

  return (
    <For each={items()}>
      {(item) => {
        const Icon = item.icon;
        const activeCls =
          item.path === "/admin" ? "bg-accent text-brand-ink shadow-sm" : "bg-brand text-brand-ink shadow-sm";
        return (
          <a
            href={item.path}
            aria-current={isActive(item.path) ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              props.onNavigate(item.path);
            }}
            class={[
              "glass-btn inline-flex items-center gap-2 rounded-xl text-sm font-medium",
              props.mobile ? "px-3.5 py-2.5" : "px-3 py-1.5",
              isActive(item.path) ? activeCls : "text-muted hover:bg-surface/80 hover:text-ink",
            ]}
          >
            <Icon class="h-4 w-4" />
            <span>{item.label}</span>
          </a>
        );
      }}
    </For>
  );
}
