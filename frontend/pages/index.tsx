import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/dashboard');
  }, [router]);
  return (
    <div style={{ textAlign: 'center', marginTop: '20%' }}>
      <h2>Redirecting to dashboard...</h2>
    </div>
  );
}
