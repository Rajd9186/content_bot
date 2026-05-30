"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

function CallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const checkAuth = useAuthStore((s) => s.checkAuth);

  const token = searchParams.get("token");

  if (token && typeof window !== "undefined") {
    localStorage.setItem("auth-token", token);
    checkAuth()
      .then(() => router.push("/dashboard"))
      .catch(() => router.push("/login"));
  }

  return (
    <div className="flex items-center gap-3">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400" />
      <p className="text-sm text-muted-foreground">Processing authentication...</p>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Suspense fallback={
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      }>
        <CallbackInner />
      </Suspense>
    </div>
  );
}
