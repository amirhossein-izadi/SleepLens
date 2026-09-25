import { cn } from "@/lib/utils";
import Image from "next/image";

interface LogoProps {
  className?: string;
  /** "mark" = icon only, "full" = icon + wordmark (white background asset). */
  variant?: "mark" | "full";
  priority?: boolean;
}

export function Logo({ className, variant = "mark", priority }: LogoProps) {
  return (
    <Image
      src={variant === "mark" ? "/brand/logo-mark.png" : "/brand/logo-full.png"}
      alt="SleepLens"
      width={variant === "mark" ? 36 : 148}
      height={36}
      priority={priority}
      className={cn(variant === "mark" ? "h-9 w-9 object-contain" : "h-9 w-auto object-contain", className)}
    />
  );
}
