import { useEffect } from "react";
import { useRouter } from "next/router";

export default function SignupPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/login");
  }, [router]);
  return (
    <div style={{ textAlign: 'center', marginTop: '20%' }}>
      <h2>Sign up is disabled. Redirecting to login...</h2>
    </div>
  );
}
