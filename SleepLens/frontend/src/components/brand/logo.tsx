import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  /** "mark" = icon only, "full" = icon + wordmark (white background asset). */
  variant?: "mark" | "full";
  priority?: boolean;
}

export function Logo({ className, variant = "mark", priority }: LogoProps) {
  const src = variant === "mark" ? "/brand/logo-mark.png" : "/brand/logo-full.png";
  return (
    // Plain img: the PNG is a fixed-ratio brand asset and next/image's
    // width/height contract fights the responsive sizing we need here.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt="SleepLens"
      width={variant === "mark" ? 36 : 148}
      height={36}
      loading={priority ? "eager" : "lazy"}
      className={cn(
        variant === "mark" ? "h-9 w-9" : "h-9 w-auto",
        "object-contain",
        className
      )}
    />
  );
}
