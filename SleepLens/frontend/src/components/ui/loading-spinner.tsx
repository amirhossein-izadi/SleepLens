import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export function LoadingSpinner({
  text,
  className,
  size = "default",
}: {
  text?: string;
  className?: string;
  size?: "default" | "lg";
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 py-12", className)}>
      <Loader2 className={cn("animate-spin text-brand-bright", size === "lg" ? "h-10 w-10" : "h-6 w-6")} />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
    </div>
  );
}

export function InlineLoader({ className }: { className?: string }) {
  return <Loader2 className={cn("h-4 w-4 animate-spin text-brand-bright", className)} />;
}
