import { FC } from 'react';
import { Header } from './Header';
import { StatCard } from './StatCard';
import { FaAnchor, FaBroadcastTower, FaDatabase, FaThermometerHalf, FaTint } from 'react-icons/fa';

interface DashboardProps {
  metrics: {
    total_floats: number;
    active_floats: number;
    total_profiles: number;
  };
  parameters: {
    avg_surface_temp: number;
    avg_surface_salinity: number;
  };
  loading: boolean;
}

export const Dashboard: FC<DashboardProps> = ({ metrics, parameters, loading }) => {
  const lastUpdated = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div
      className="min-h-screen bg-cover bg-center"
      style={{
        backgroundImage:
          'url("https://www.transparenttextures.com/patterns/cubes.png"), linear-gradient(135deg, #06202e 0%, #08354e 25%, #0a5d84 50%, #1280af 75%, #179ddb 100%)',
      }}
    >
      <div className="bg-black/20 min-h-screen">
        <Header lastUpdated={lastUpdated} />
        <main className="container-fluid mx-auto px-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            <StatCard
              icon={<FaAnchor />}
              title="Total Floats"
              value={metrics.total_floats.toLocaleString()}
              loading={loading}
              color="text-violet-400"
            />
            <StatCard
              icon={<FaBroadcastTower />}
              title="Active Floats"
              value={metrics.active_floats.toLocaleString()}
              loading={loading}
              color="text-green-400"
            />
            <StatCard
              icon={<FaDatabase />}
              title="Total Profiles"
              value={`${(metrics.total_profiles / 1000000).toFixed(1)}M`}
              loading={loading}
              color="text-orange-400"
            />
            <StatCard
              icon={<FaThermometerHalf />}
              title="Avg SST"
              value={`${parameters.avg_surface_temp.toFixed(1)} °C`}
              loading={loading}
              color="text-red-400"
            />
            <StatCard
              icon={<FaTint />}
              title="Avg SSS"
              value={`${parameters.avg_surface_salinity.toFixed(1)} psu`}
              loading={loading}
              color="text-cyan-400"
            />
          </div>
        </main>
      </div>
    </div>
  );
};
