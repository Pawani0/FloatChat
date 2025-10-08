import { X, Thermometer, Ruler, TrendingDown, Filter } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Settings } from '../types/ocean';

interface SettingsPanelProps {
  settings: Settings;
  onSettingsChange: (settings: Settings) => void;
  onClose: () => void;
}

export function SettingsPanel({ settings, onSettingsChange, onClose }: SettingsPanelProps) {
  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    onSettingsChange({ ...settings, [key]: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <Card className="mx-4 w-full max-w-md border-white/10 bg-[#04060f]/95 shadow-2xl">
        <CardHeader className="border-b border-white/10">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg text-white">Visualization Settings</CardTitle>
              <CardDescription className="text-gray-400">
                Customize your data visualization preferences
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 text-gray-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 p-6">
          {/* Units */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-medium text-white">
              <Thermometer className="h-4 w-4 text-cyan-400" />
              Units
            </label>
            <div className="space-y-2.5">
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 transition-all hover:border-cyan-400/30 hover:bg-white/[0.06] has-[:checked]:border-cyan-400/50 has-[:checked]:bg-cyan-500/10">
                <input
                  type="radio"
                  name="units"
                  value="metric"
                  checked={settings.units === 'metric'}
                  onChange={(e) => updateSetting('units', e.target.value as 'metric' | 'imperial')}
                  className="h-4 w-4 border-white/20 bg-white/10 text-cyan-500 focus:ring-cyan-500"
                />
                <span className="text-sm text-gray-300">Metric (°C, m, PSU)</span>
              </label>
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 transition-all hover:border-cyan-400/30 hover:bg-white/[0.06] has-[:checked]:border-cyan-400/50 has-[:checked]:bg-cyan-500/10">
                <input
                  type="radio"
                  name="units"
                  value="imperial"
                  checked={settings.units === 'imperial'}
                  onChange={(e) => updateSetting('units', e.target.value as 'metric' | 'imperial')}
                  className="h-4 w-4 border-white/20 bg-white/10 text-cyan-500 focus:ring-cyan-500"
                />
                <span className="text-sm text-gray-300">Imperial (°F, ft)</span>
              </label>
            </div>
          </div>

          <Separator className="bg-white/10" />

          {/* Depth Axis */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-medium text-white">
              <TrendingDown className="h-4 w-4 text-cyan-400" />
              Depth Axis
            </label>
            <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 transition-all hover:border-cyan-400/30 hover:bg-white/[0.06]">
              <input
                type="checkbox"
                checked={settings.reverseDepthAxis}
                onChange={(e) => updateSetting('reverseDepthAxis', e.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-white/10 text-cyan-500 focus:ring-cyan-500"
              />
              <div className="flex-1">
                <span className="text-sm text-gray-300">Reverse depth axis</span>
                <p className="mt-0.5 text-xs text-gray-500">
                  Oceanographic convention (0m at top, deeper values below)
                </p>
              </div>
            </label>
          </div>

          <Separator className="bg-white/10" />

          {/* Smoothing */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-medium text-white">
              <Filter className="h-4 w-4 text-cyan-400" />
              Data Processing
            </label>
            <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 transition-all hover:border-cyan-400/30 hover:bg-white/[0.06]">
              <input
                type="checkbox"
                checked={settings.smoothing}
                onChange={(e) => updateSetting('smoothing', e.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-white/10 text-cyan-500 focus:ring-cyan-500"
              />
              <span className="text-sm text-gray-300">Apply smoothing to profiles</span>
            </label>
          </div>

          <Separator className="bg-white/10" />

          {/* Downsampling */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-medium text-white">
              <Ruler className="h-4 w-4 text-cyan-400" />
              Downsampling
            </label>
            <select
              value={settings.downsampling}
              onChange={(e) => updateSetting('downsampling', parseInt(e.target.value))}
              className="w-full rounded-lg border border-white/10 bg-white/[0.05] px-3 py-2.5 text-sm text-gray-300 focus:border-cyan-400/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20"
            >
              <option value={1} className="bg-[#04060f] text-gray-300">
                No downsampling
              </option>
              <option value={2} className="bg-[#04060f] text-gray-300">
                Every 2nd point
              </option>
              <option value={5} className="bg-[#04060f] text-gray-300">
                Every 5th point
              </option>
              <option value={10} className="bg-[#04060f] text-gray-300">
                Every 10th point
              </option>
            </select>
            <p className="text-xs text-gray-500">
              Reduce data density for faster rendering of large datasets
            </p>
          </div>
        </CardContent>

        <div className="border-t border-white/10 p-4">
          <Button
            onClick={onClose}
            className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-400 hover:to-cyan-400"
          >
            Apply Settings
          </Button>
        </div>
      </Card>
    </div>
  );
}
 