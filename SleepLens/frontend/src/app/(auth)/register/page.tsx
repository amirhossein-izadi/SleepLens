import { AuthForm } from "@/components/auth/auth-form";
import { BrandPanel } from "@/components/auth/brand-panel";

export default function RegisterPage() {
  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <div className="flex items-center justify-center px-6 py-12">
        <AuthForm mode="register" />
      </div>
      <BrandPanel />
    </div>
  );
}
