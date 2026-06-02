'use client';

import { Gauge, RefreshCw } from 'lucide-react';
import { ProviderDashboard } from '@/components/providers/ProviderDashboard';

export function OperationsSection() {
  return (
    <div className="h-full overflow-y-auto">
      <ProviderDashboard />
    </div>
  );
}