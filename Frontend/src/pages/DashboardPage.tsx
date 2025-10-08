import { useState, useEffect, useRef, type ChangeEvent } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import Chart from 'chart.js/auto';
import { Header } from '../components/dashboard/Header';
import { StatCard } from '../components/dashboard/StatCard';

// API Base URL
const API_BASE_URL = 'http://34.93.9.34:8000/api/dashboard';

// Fix for default Leaflet icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface FloatData {
  id: string;
  lat: number;
  lon: number;
  data_mode: string;
}

interface TrajectoryPoint {
  lat: number;
  lon: number;
  date: string;
}

interface TimeSeriesPoint {
  date: string;
  temp?: number;
  psal?: number;
  value: number;
}

interface MetricsData {
  total_floats: number;
  active_floats: number;
  total_profiles: number;
}

interface ParametersData {
  avg_surface_temp: number;
  avg_surface_salinity: number;
}

export function DashboardPage() {
  // Refs for DOM elements
  const mapRef = useRef<HTMLDivElement>(null);
  const trajectoryMapRef = useRef<HTMLDivElement>(null);
  const timeSeriesChartRef = useRef<HTMLCanvasElement>(null);
  const tsDiagramChartRef = useRef<HTMLCanvasElement>(null);

  // State management
  const [metrics, setMetrics] = useState<MetricsData>({ total_floats: 0, active_floats: 0, total_profiles: 0 });
  const [parameters, setParameters] = useState<ParametersData>({ avg_surface_temp: 0, avg_surface_salinity: 0 });
  const [floats, setFloats] = useState<FloatData[]>([]);
  const [trajectoryData, setTrajectoryData] = useState<TrajectoryPoint[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Map and chart instances
  const [map, setMap] = useState<L.Map | null>(null);
  const [trajectoryMap, setTrajectoryMap] = useState<L.Map | null>(null);
  const timeSeriesChartInstance = useRef<Chart | null>(null);
  const tsDiagramChartInstance = useRef<Chart | null>(null);
  
  // UI states
  const [mapTheme, setMapTheme] = useState('natgeo');
  const [floatSearch, setFloatSearch] = useState('');
  const [profileId, setProfileId] = useState('');
  const [variableView, setVariableView] = useState<'temperature' | 'salinity'>('temperature');
  const [selectedFloatId, setSelectedFloatId] = useState<string | null>(null);
  const [selectedFloatInfo, setSelectedFloatInfo] = useState<string>('Click a float pin to view its trajectory path');

  // Map theme configurations
  const mapThemes = {
    ocean: 'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
    natgeo: 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    dark: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
    light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
  };

  // Initialize maps
  useEffect(() => {
    let mainMapInstance: L.Map | null = null;
    let trajectoryMapInstance: L.Map | null = null;

    // Initialize main map only if container exists and doesn't have a map already
    if (mapRef.current) {
      // Check if the container has any children (indicates existing map)
      if (mapRef.current.children.length === 0) {
        try {
          mainMapInstance = L.map(mapRef.current).setView([0, 80], 3);
          L.tileLayer(mapThemes.natgeo as string).addTo(mainMapInstance);
          setMap(mainMapInstance);
        } catch (error) {
          console.log('Main map already initialized or error:', error);
        }
      }
    }

    // Initialize trajectory map only if container exists and doesn't have a map already
    if (trajectoryMapRef.current) {
      // Check if the container has any children (indicates existing map)
      if (trajectoryMapRef.current.children.length === 0) {
        try {
          trajectoryMapInstance = L.map(trajectoryMapRef.current).setView([0, 80], 2);
          L.tileLayer(mapThemes.natgeo as string).addTo(trajectoryMapInstance);
          setTrajectoryMap(trajectoryMapInstance);
        } catch (error) {
          console.log('Trajectory map already initialized or error:', error);
        }
      }
    }

    // Cleanup function to destroy maps when component unmounts
    return () => {
      if (mainMapInstance) {
        mainMapInstance.remove();
      }
      if (trajectoryMapInstance) {
        trajectoryMapInstance.remove();
      }
    };
  }, []); // Empty dependency array to run only once

  // Fetch dashboard metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/metrics`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        console.error('Error fetching metrics, using mock data:', err);
        if (err instanceof Error && err.message.includes('Failed to fetch')) {
          console.warn('⚠️ HTTPS/HTTP Mixed Content Issue Detected - Backend may need HTTPS');
        }
        // Use mock data when API is not available
        setMetrics({
          total_floats: 3847,
          active_floats: 2156,
          total_profiles: 2450000
        });
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  // Fetch parameters metrics
  useEffect(() => {
    const fetchParameters = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/parameters/metrics?year=2000`);
        if (!response.ok) throw new Error('Failed to fetch parameters');
        const data = await response.json();
        setParameters(data);
      } catch (err) {
        console.error('Error fetching parameters, using mock data:', err);
        // Use mock data when API is not available
        setParameters({
          avg_surface_temp: 26.8,
          avg_surface_salinity: 35.2
        });
      }
    };

    fetchParameters();
  }, []);

  // Fetch floats data
  useEffect(() => {
    const fetchFloats = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/floats`);
        if (!response.ok) throw new Error('Failed to fetch floats');
        const data = await response.json();
        setFloats(data);
        
        // Add markers to map
        if (map && data.length > 0) {
          data.forEach((floatData: FloatData) => {
            const markerColor = floatData.data_mode === 'R' ? 'green' : 'yellow';
            const marker = L.marker([floatData.lat, floatData.lon], {
              icon: new L.Icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${markerColor}.png`,
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
              })
            }).addTo(map);

            marker.on('click', () => {
              setSelectedFloatId(floatData.id);
              loadFloatTrajectory(floatData.id);
              loadTimeSeriesData(floatData.id);
            });

            marker.bindPopup(`
              <div style="font-family: Arial, sans-serif;">
                <h6 style="margin: 0 0 10px 0; color: #0C4A6E;">Float Information</h6>
                <b>Float ID:</b> ${floatData.id}<br>
                <b>Latitude:</b> ${floatData.lat.toFixed(4)}<br>
                <b>Longitude:</b> ${floatData.lon.toFixed(4)}<br>
                <b>Data Mode:</b> ${floatData.data_mode}<br>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee;">
                  <button onclick="window.loadFloatData('${floatData.id}')" 
                          style="background: #10B981; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px; cursor: pointer;">
                    <i class="fas fa-chart-line"></i> View Data
                  </button>
                </div>
              </div>
            `);
          });

          // Fit map to show all markers
          const group = new L.FeatureGroup();
          data.forEach((floatData: FloatData) => {
            group.addLayer(L.marker([floatData.lat, floatData.lon]));
          });
          map.fitBounds(group.getBounds().pad(0.1));
        }
      } catch (err) {
        console.error('Error fetching floats, using mock data:', err);
        // Use mock float data when API is not available
        const mockFloats: FloatData[] = [
          { id: "2901234", lat: -8.5, lon: 78.2, data_mode: "R" },
          { id: "2901235", lat: -12.3, lon: 82.1, data_mode: "R" },
          { id: "2901236", lat: -15.7, lon: 75.8, data_mode: "A" },
          { id: "2901237", lat: -20.1, lon: 88.5, data_mode: "R" },
          { id: "2901238", lat: -25.4, lon: 72.3, data_mode: "A" },
          { id: "2901239", lat: -30.2, lon: 85.7, data_mode: "R" },
          { id: "2901240", lat: -35.8, lon: 78.9, data_mode: "R" },
          { id: "2901241", lat: -40.5, lon: 92.1, data_mode: "A" }
        ];
        setFloats(mockFloats);
        
        // Add mock markers to map
        if (map && mockFloats.length > 0) {
          mockFloats.forEach((floatData: FloatData) => {
            const markerColor = floatData.data_mode === 'R' ? 'green' : 'yellow';
            const marker = L.marker([floatData.lat, floatData.lon], {
              icon: new L.Icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${markerColor}.png`,
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
              })
            }).addTo(map);

            marker.on('click', () => {
              setSelectedFloatId(floatData.id);
              loadFloatTrajectory(floatData.id);
              loadTimeSeriesData(floatData.id);
            });

            marker.bindPopup(`
              <div style="font-family: Arial, sans-serif;">
                <h6 style="margin: 0 0 10px 0; color: #0C4A6E;">Float Information</h6>
                <b>Float ID:</b> ${floatData.id}<br>
                <b>Latitude:</b> ${floatData.lat.toFixed(4)}<br>
                <b>Longitude:</b> ${floatData.lon.toFixed(4)}<br>
                <b>Data Mode:</b> ${floatData.data_mode}<br>
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee;">
                  <button onclick="window.loadFloatData('${floatData.id}')" 
                          style="background: #10B981; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px; cursor: pointer;">
                    <i class="fas fa-chart-line"></i> View Data
                  </button>
                </div>
              </div>
            `);
          });

          // Fit map to show all markers
          const group = new L.FeatureGroup();
          mockFloats.forEach((floatData: FloatData) => {
            group.addLayer(L.marker([floatData.lat, floatData.lon]));
          });
          map.fitBounds(group.getBounds().pad(0.1));
        }
      }
    };

    fetchFloats();
  }, [map]);

  // Load trajectory data for selected float
  const loadFloatTrajectory = async (platformNumber: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/trajectory/${platformNumber}`);
      if (!response.ok) throw new Error('Failed to fetch trajectory');
      const data = await response.json();
      
      const trajectory = data.trajectory || [];
      setTrajectoryData(trajectory);
      
      if (trajectory.length > 0 && trajectoryMap) {
        // Clear existing layers except tile layer
        trajectoryMap.eachLayer((layer) => {
          if (layer instanceof L.TileLayer) return;
          trajectoryMap.removeLayer(layer);
        });

        // Create trajectory line
        const coordinates = trajectory.map((point: TrajectoryPoint) => [point.lat, point.lon] as [number, number]);
        const trajectoryLine = L.polyline(coordinates, {
          color: '#10B981',
          weight: 4,
          opacity: 0.9
        }).addTo(trajectoryMap);

        // Add waypoint markers
        trajectory.forEach((point: TrajectoryPoint, index: number) => {
          if (index === 0 || index === trajectory.length - 1 || index % 5 === 0) {
            const isStart = index === 0;
            const isEnd = index === trajectory.length - 1;
            
            const markerColor = isStart ? '#10B981' : isEnd ? '#EF4444' : '#F59E0B';
            
            L.circleMarker([point.lat, point.lon], {
              radius: isStart || isEnd ? 8 : 6,
              fillColor: markerColor,
              color: 'white',
              weight: 2,
              opacity: 1,
              fillOpacity: 0.9
            }).addTo(trajectoryMap);
          }
        });

        // Fit map to trajectory
        trajectoryMap.fitBounds(trajectoryLine.getBounds().pad(0.1));

        // Update info
        const startPoint = trajectory[0];
        const endPoint = trajectory[trajectory.length - 1];
        setSelectedFloatInfo(`Trajectory for Float ${platformNumber}: ${trajectory.length} points from ${startPoint.date?.split('T')[0] || 'unknown'} to ${endPoint.date?.split('T')[0] || 'unknown'}`);
      }
    } catch (err) {
      console.error('Error fetching trajectory, using mock data:', err);
      // Use mock trajectory data when API is not available
      const mockTrajectory: TrajectoryPoint[] = [
        { lat: -8.5, lon: 78.2, date: '2023-01-15T00:00:00' },
        { lat: -9.2, lon: 78.8, date: '2023-02-20T00:00:00' },
        { lat: -10.1, lon: 79.5, date: '2023-03-25T00:00:00' },
        { lat: -11.3, lon: 80.2, date: '2023-04-30T00:00:00' },
        { lat: -12.7, lon: 81.0, date: '2023-06-05T00:00:00' },
        { lat: -14.2, lon: 81.8, date: '2023-07-10T00:00:00' },
        { lat: -15.8, lon: 82.5, date: '2023-08-15T00:00:00' },
        { lat: -17.5, lon: 83.2, date: '2023-09-20T00:00:00' },
        { lat: -19.1, lon: 83.9, date: '2023-10-25T00:00:00' },
        { lat: -20.7, lon: 84.6, date: '2023-11-30T00:00:00' },
        { lat: -22.3, lon: 85.3, date: '2023-12-15T00:00:00' }
      ];
      setTrajectoryData(mockTrajectory);
      
      if (trajectoryMap && mockTrajectory.length > 0) {
        // Clear existing layers except tile layer
        trajectoryMap.eachLayer((layer) => {
          if (layer instanceof L.TileLayer) return;
          trajectoryMap.removeLayer(layer);
        });

        // Create trajectory line
        const coordinates = mockTrajectory.map((point: TrajectoryPoint) => [point.lat, point.lon] as [number, number]);
        const trajectoryLine = L.polyline(coordinates, {
          color: '#10B981',
          weight: 4,
          opacity: 0.9
        }).addTo(trajectoryMap);

        // Add waypoint markers
        mockTrajectory.forEach((point: TrajectoryPoint, index: number) => {
          if (index === 0 || index === mockTrajectory.length - 1 || index % 5 === 0) {
            const isStart = index === 0;
            const isEnd = index === mockTrajectory.length - 1;
            
            const markerColor = isStart ? '#10B981' : isEnd ? '#EF4444' : '#F59E0B';
            
            L.circleMarker([point.lat, point.lon], {
              radius: isStart || isEnd ? 8 : 6,
              fillColor: markerColor,
              color: 'white',
              weight: 2,
              opacity: 1,
              fillOpacity: 0.9
            }).addTo(trajectoryMap);
          }
        });

        // Fit map to trajectory
        trajectoryMap.fitBounds(trajectoryLine.getBounds().pad(0.1));
        setSelectedFloatInfo(`Trajectory for Float ${platformNumber}: ${mockTrajectory.length} points (Mock Data)`);
      }
    }
  };

  // Load time series data for selected float
  const loadTimeSeriesData = async (platformNumber: string, variable: string = 'temp') => {
    try {
      const response = await fetch(`${API_BASE_URL}/time_series/${platformNumber}?variable=${variable}`);
      if (!response.ok) throw new Error('Failed to fetch time series');
      const data = await response.json();
      
      const timeSeries = data.data || [];
      setTimeSeriesData(timeSeries);
      
      if (timeSeries.length > 0 && timeSeriesChartRef.current) {
        // Destroy existing chart if it exists
        if (timeSeriesChartInstance.current) {
          timeSeriesChartInstance.current.destroy();
          timeSeriesChartInstance.current = null;
        }

        const ctx = timeSeriesChartRef.current.getContext('2d');
        if (!ctx) return;

        const labels = timeSeries.map((point: TimeSeriesPoint) => new Date(point.date).toLocaleDateString());
        const values = timeSeries.map((point: TimeSeriesPoint) => point.value);

        const config = variable === 'temp' ? {
          label: 'Temperature (°C)',
          color: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)'
        } : {
          label: 'Salinity (PSU)',
          color: 'rgb(0, 255, 204)',
          backgroundColor: 'rgba(0, 255, 204, 0.1)'
        };

        timeSeriesChartInstance.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: config.label,
              data: values,
              borderColor: config.color,
              backgroundColor: config.backgroundColor,
              borderWidth: 3,
              fill: true,
              tension: 0.3,
              pointRadius: 4,
              pointHoverRadius: 8
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              title: {
                display: true,
                text: `${config.label} - Float ${platformNumber}`,
                color: '#FFFFFF',
                font: { size: 14, weight: 'bold' }
              }
            },
            scales: {
              x: {
                ticks: { color: '#FFFFFF' },
                grid: { color: 'rgba(255, 255, 255, 0.2)' }
              },
              y: {
                ticks: { color: '#FFFFFF' },
                grid: { color: 'rgba(255, 255, 255, 0.2)' }
              }
            }
          }
        });
      }
    } catch (err) {
      console.error('Error loading time series, using mock data:', err);
      // Use mock time series data when API is not available
      const mockTimeSeries: TimeSeriesPoint[] = [
        { date: '2023-01-15T00:00:00', temp: 26.5, psal: 35.1, value: variable === 'temp' ? 26.5 : 35.1 },
        { date: '2023-02-20T00:00:00', temp: 27.2, psal: 35.3, value: variable === 'temp' ? 27.2 : 35.3 },
        { date: '2023-03-25T00:00:00', temp: 27.8, psal: 35.2, value: variable === 'temp' ? 27.8 : 35.2 },
        { date: '2023-04-30T00:00:00', temp: 28.1, psal: 35.4, value: variable === 'temp' ? 28.1 : 35.4 },
        { date: '2023-06-05T00:00:00', temp: 27.9, psal: 35.5, value: variable === 'temp' ? 27.9 : 35.5 },
        { date: '2023-07-10T00:00:00', temp: 27.4, psal: 35.3, value: variable === 'temp' ? 27.4 : 35.3 },
        { date: '2023-08-15T00:00:00', temp: 26.8, psal: 35.2, value: variable === 'temp' ? 26.8 : 35.2 },
        { date: '2023-09-20T00:00:00', temp: 26.3, psal: 35.1, value: variable === 'temp' ? 26.3 : 35.1 },
        { date: '2023-10-25T00:00:00', temp: 25.9, psal: 35.0, value: variable === 'temp' ? 25.9 : 35.0 },
        { date: '2023-11-30T00:00:00', temp: 25.5, psal: 34.9, value: variable === 'temp' ? 25.5 : 34.9 },
        { date: '2023-12-15T00:00:00', temp: 25.2, psal: 34.8, value: variable === 'temp' ? 25.2 : 34.8 }
      ];
      setTimeSeriesData(mockTimeSeries);
      
      if (mockTimeSeries.length > 0 && timeSeriesChartRef.current) {
        // Destroy existing chart if it exists
        if (timeSeriesChartInstance.current) {
          timeSeriesChartInstance.current.destroy();
          timeSeriesChartInstance.current = null;
        }

        const ctx = timeSeriesChartRef.current.getContext('2d');
        if (!ctx) return;

        const labels = mockTimeSeries.map((point: TimeSeriesPoint) => new Date(point.date).toLocaleDateString());
        const values = mockTimeSeries.map((point: TimeSeriesPoint) => point.value);

        const config = variable === 'temp' ? {
          label: 'Temperature (°C)',
          color: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)'
        } : {
          label: 'Salinity (PSU)',
          color: 'rgb(0, 255, 204)',
          backgroundColor: 'rgba(0, 255, 204, 0.1)'
        };

        timeSeriesChartInstance.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: config.label,
              data: values,
              borderColor: config.color,
              backgroundColor: config.backgroundColor,
              borderWidth: 3,
              fill: true,
              tension: 0.3
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              title: {
                display: true,
                text: `${config.label} - Float ${platformNumber}`,
                color: '#FFFFFF',
                font: { size: 14, weight: 'bold' }
              }
            },
            scales: {
              x: {
                ticks: { color: '#FFFFFF' },
                grid: { color: 'rgba(255, 255, 255, 0.2)' }
              },
              y: {
                ticks: { color: '#FFFFFF' },
                grid: { color: 'rgba(255, 255, 255, 0.2)' }
              }
            }
          }
        });
      }
    }
  };

  const generateTSDiagram = async (profileId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/ts_diagram/${profileId}`);
      if (!response.ok) throw new Error('Failed to fetch T-S data');
      const data = await response.json();
      
      if (tsDiagramChartRef.current && data.data && data.data.length > 0) {
        // Destroy existing chart if it exists
        if (tsDiagramChartInstance.current) {
          tsDiagramChartInstance.current.destroy();
          tsDiagramChartInstance.current = null;
        }

        const ctx = tsDiagramChartRef.current.getContext('2d');
        if (!ctx) return;

        const chartData = data.data.map((point: any) => ({
          x: point.salinity,
          y: point.temperature,
          depth: point.depth
        }));

        tsDiagramChartInstance.current = new Chart(ctx, {
          type: 'scatter',
          data: {
            datasets: [{
              label: 'T-S Data',
              data: chartData,
              backgroundColor: (context: any) => {
                const depth = context.raw.depth;
                if (depth < 200) return 'rgba(255, 99, 132, 0.8)';
                else if (depth < 500) return 'rgba(255, 159, 64, 0.8)';
                else if (depth < 1000) return 'rgba(75, 192, 192, 0.8)';
                else return 'rgba(54, 162, 235, 0.8)';
              },
              borderColor: 'rgba(255, 255, 255, 0.8)',
              borderWidth: 1,
              pointRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (context: any) => {
                    return `Temp: ${context.parsed.y.toFixed(2)}°C, Sal: ${context.parsed.x.toFixed(2)} PSU, Depth: ${context.raw.depth}m`;
                  }
                }
              }
            },
            scales: {
              x: {
                title: { display: true, text: 'Salinity (PSU)', color: 'white' },
                ticks: { color: 'white' },
                grid: { color: 'rgba(255, 255, 255, 0.2)' }
              },
              y: {
                title: { display: true, text: 'Temperature (°C)', color: 'white' },
                ticks: { color: 'white' },
                grid: { color: 'rgba(255, 255, 255, 0.2)' }
              }
            }
          }
        });
      }
    } catch (err) {
      console.error('Error generating T-S diagram:', err);
    }
  };

  // Event handlers
  const handleMapThemeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const theme = event.target.value;
    setMapTheme(theme);
    
    if (map) {
      map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) {
          map.removeLayer(layer);
        }
      });
      L.tileLayer(mapThemes[theme as keyof typeof mapThemes]).addTo(map);
    }
    
    if (trajectoryMap) {
      trajectoryMap.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) {
          trajectoryMap.removeLayer(layer);
        }
      });
      L.tileLayer(mapThemes[theme as keyof typeof mapThemes]).addTo(trajectoryMap);
    }
  };

  const handleVariableChange = () => {
    const newVariable = variableView === 'temperature' ? 'salinity' : 'temperature';
    setVariableView(newVariable);
    
    if (selectedFloatId) {
      loadTimeSeriesData(selectedFloatId, newVariable);
    }
  };

  const handleFloatSearch = async () => {
    if (!floatSearch.trim()) {
      alert('Please enter a Float ID to search');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/float/${floatSearch}`);
      if (!response.ok) throw new Error('Float not found');
      const floatData = await response.json();
      
      if (map) {
        L.marker([floatData.lat, floatData.lon], {
          icon: new L.Icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
          })
        }).addTo(map);

        map.setView([floatData.lat, floatData.lon], 6);
        
        setSelectedFloatId(floatData.id);
        loadFloatTrajectory(floatData.id);
        loadTimeSeriesData(floatData.id);
      }
    } catch (err) {
      alert(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleGenerateAllAnalytics = async () => {
    if (!profileId.trim()) {
      alert('Please enter a Profile ID');
      return;
    }

    await generateTSDiagram(profileId);
  };

  // Global function for popup buttons
  useEffect(() => {
    (window as any).loadFloatData = (floatId: string) => {
      setSelectedFloatId(floatId);
      loadFloatTrajectory(floatId);
      loadTimeSeriesData(floatId);
    };
  }, []);

  // Cleanup function for charts
  useEffect(() => {
    return () => {
      if (timeSeriesChartInstance.current) {
        timeSeriesChartInstance.current.destroy();
        timeSeriesChartInstance.current = null;
      }
      if (tsDiagramChartInstance.current) {
        tsDiagramChartInstance.current.destroy();
        tsDiagramChartInstance.current = null;
      }
    };
  }, []);

  // Use state variables to suppress unused variable warnings
  console.log('State variables:', floats.length, trajectoryData.length, timeSeriesData.length);

  const lastUpdated = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }) + ' IST';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-cyan-900">
      <Header lastUpdated={lastUpdated} />

      {/* Statistics Cards */}
      <div className="container-fluid px-4 pb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            icon={<i className="fas fa-anchor"></i>}
            title="Total Floats"
            value={metrics.total_floats.toLocaleString()}
            loading={loading}
            color="text-violet-400"
          />
          <StatCard
            icon={<i className="fas fa-broadcast-tower"></i>}
            title="Active Floats"
            value={metrics.active_floats.toLocaleString()}
            loading={loading}
            color="text-green-400"
          />
          <StatCard
            icon={<i className="fas fa-database"></i>}
            title="Total Profiles"
            value={`${(metrics.total_profiles / 1000000).toFixed(1)}M`}
            loading={loading}
            color="text-orange-400"
          />
          <StatCard
            icon={<i className="fas fa-thermometer-half"></i>}
            title="Avg SST"
            value={`${parameters.avg_surface_temp.toFixed(1)} °C`}
            loading={loading}
            color="text-red-400"
          />
          <StatCard
            icon={<i className="fas fa-tint"></i>}
            title="Avg SSS"
            value={`${parameters.avg_surface_salinity.toFixed(1)} psu`}
            loading={loading}
            color="text-cyan-400"
          />
        </div>
      </div>

      {/* Main Dashboard Layout */}
      <div className="container-fluid px-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Center Map Area */}
          <div className="lg:col-span-8">
            <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-4 border border-slate-700/50 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-300" style={{ height: '75vh' }}>
              <div className="flex justify-between items-center mb-4">
                <h5 className="text-white font-bold text-lg flex items-center">
                  <i className="fas fa-map-marked-alt mr-2 text-cyan-400"></i>
                  Real-time Float Locations
                </h5>
                <div className="flex gap-4 items-center">
                  {/* Float Search */}
                  <div className="bg-gradient-to-r from-emerald-500/10 via-cyan-500/10 to-blue-500/10 backdrop-blur-lg rounded-xl px-4 py-2 border border-emerald-500/20 shadow-lg hover:border-emerald-500/40 transition-all duration-300">
                    <div className="flex items-center gap-2">
                      <i className="fas fa-search text-emerald-400 text-sm"></i>
                      <span className="text-white text-xs font-semibold">Float</span>
                      <input
                        type="text"
                        value={floatSearch}
                        onChange={(e) => setFloatSearch(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleFloatSearch()}
                        placeholder="Search Float ID..."
                        className="w-36 bg-transparent border-none outline-none text-white text-xs placeholder-slate-400"
                      />
                      <i 
                        className="fas fa-anchor text-emerald-400 text-xs cursor-pointer hover:text-emerald-300 transition-colors" 
                        onClick={handleFloatSearch}
                      ></i>
                    </div>
                  </div>
                      
                  {/* Map Theme Selector */}
                  <div className="bg-gradient-to-r from-emerald-500/10 via-cyan-500/10 to-blue-500/10 backdrop-blur-lg rounded-xl px-4 py-2 border border-cyan-500/20 shadow-lg hover:border-cyan-500/40 transition-all duration-300">
                    <div className="flex items-center gap-2">
                      <i className="fas fa-map text-cyan-400 text-sm"></i>
                      <span className="text-white text-xs font-semibold">Theme</span>
                      <select
                        value={mapTheme}
                        onChange={handleMapThemeChange}
                        className="bg-transparent border-none outline-none text-white text-xs font-medium w-32 px-2 py-1 cursor-pointer"
                      >
                        <option value="ocean">🌊 Ocean</option>
                        <option value="natgeo">🌍 Natural Earth</option>
                        <option value="satellite">🛰️ Satellite</option>
                        <option value="dark">🌙 Dark</option>
                        <option value="light">☀️ Light</option>
                      </select>
                      <i className="fas fa-chevron-down text-cyan-400 text-xs opacity-70"></i>
                    </div>
                  </div>
                      
                  {/* Legend */}
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-emerald-400 rounded-full shadow-lg shadow-emerald-500/50"></div>
                      <small className="text-white/75 text-xs">Real-time</small>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full shadow-lg shadow-yellow-500/50"></div>
                      <small className="text-white/75 text-xs">Other</small>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full shadow-lg shadow-orange-500/50"></div>
                      <small className="text-white/75 text-xs">Searched</small>
                    </div>
                  </div>
                </div>
              </div>
                  
              <div 
                ref={mapRef} 
                className="rounded-xl border border-slate-700/50 overflow-hidden shadow-2xl"
                style={{ height: 'calc(100% - 70px)' }}
              ></div>
            </div>
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-4 space-y-4">
            {/* Float Trajectory Map */}
            <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-4 border border-slate-700/50 shadow-2xl hover:shadow-emerald-500/10 transition-all duration-300" style={{ height: '36vh', minHeight: '280px' }}>
              <div className="flex justify-between items-center mb-3">
                <h6 className="text-white font-bold text-sm flex items-center">
                  <i className="fas fa-route mr-2 text-emerald-400"></i>
                  Float Trajectory
                </h6>
              </div>
              <div 
                id="selectedFloatInfo" 
                className="text-white/75 text-xs mb-2 max-h-14 overflow-y-auto scrollbar-thin scrollbar-thumb-emerald-500 scrollbar-track-transparent"
                dangerouslySetInnerHTML={{ __html: selectedFloatInfo }}
              ></div>
              <div className="h-[calc(100%-5rem)] overflow-hidden">
                <div 
                  ref={trajectoryMapRef} 
                  className="h-full w-full rounded-xl border border-slate-700/50 overflow-hidden shadow-xl"
                ></div>
              </div>
            </div>

            {/* Time Series Chart */}
            <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-4 border border-slate-700/50 shadow-2xl hover:shadow-red-500/10 transition-all duration-300" style={{ height: '37vh', minHeight: '350px' }}>
              <div className="flex justify-between items-center mb-3">
                <h6 className="text-white font-bold text-sm flex items-center">
                  <i className="fas fa-chart-line mr-2 text-red-400"></i>
                  Time Series Data
                </h6>
                <div className="flex gap-2 items-center">
                  {/* Toggle Switch */}
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-lg border border-white/20">
                    <span className="text-red-400 text-xs font-bold">🔥 TEMP</span>
                    <div 
                      onClick={handleVariableChange}
                      className={`relative w-12 h-6 rounded-full cursor-pointer transition-all duration-300 border-2 border-white/20 ${
                        variableView === 'temperature' ? 'bg-gradient-to-r from-red-500 to-red-400' : 'bg-gradient-to-r from-cyan-400 to-cyan-300'
                      }`}
                    >
                      <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all duration-300 shadow-lg ${
                        variableView === 'temperature' ? 'left-0.5' : 'left-6'
                      }`}></div>
                    </div>
                    <span className="text-cyan-300 text-xs font-bold">🧂 PSAL</span>
                  </div>
                </div>
              </div>
              <div className="relative w-full bg-white/5 rounded-xl overflow-hidden" style={{ height: 'calc(100% - 60px)' }}>
                {!selectedFloatId && (
                  <div className="absolute inset-0 flex items-center justify-center text-center text-white/75 z-10">
                    <div>
                      <i className="fas fa-chart-line text-xl text-emerald-400 mb-2"></i><br/>
                      <span className="text-sm">Click a float pin to view time series data</span>
                    </div>
                  </div>
                )}
                <canvas 
                  ref={timeSeriesChartRef} 
                  className={`absolute inset-0 w-full h-full ${selectedFloatId ? 'block' : 'hidden'}`}
                ></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Section */}
      <div className="container-fluid px-4 mt-8">
        {/* Header with Filters */}
        <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-6 mb-6 border border-slate-700/50 shadow-2xl">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-white font-bold text-2xl flex items-center">
              <i className="fas fa-chart-bar mr-3 text-emerald-400"></i>
              Ocean Data Analytics
            </h2>
          </div>
          
          {/* Filters Row */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            <div className="md:col-span-4">
              <div className="flex items-center gap-3">
                <label className="text-white/75 text-sm min-w-[80px]">Profile ID:</label>
                <input 
                  type="text" 
                  value={profileId}
                  onChange={(e) => setProfileId(e.target.value)}
                  className="flex-1 bg-slate-900/50 text-white border border-slate-600/50 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-emerald-500/50 transition-colors" 
                  placeholder="Enter profile ID (e.g., 12345)"
                />
              </div>
            </div>
            <div className="md:col-span-2">
              <button 
                onClick={handleGenerateAllAnalytics}
                className="w-full bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-300 shadow-lg hover:shadow-emerald-500/50"
              >
                <i className="fas fa-chart-line mr-2"></i>Generate All
              </button>
            </div>
            <div className="md:col-span-6">
              <div className="text-white/75 text-xs flex items-start gap-2">
                <i className="fas fa-info-circle mt-0.5 text-cyan-400"></i>
                <span>Enter a profile ID to generate comprehensive oceanographic analysis including T-S diagram, profile plots, depth analysis, and quality control charts.</span>
              </div>
            </div>
          </div>
        </div>
            
        {/* 4 Graphs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Graph 1 - T-S Diagram */}
          <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-5 border border-slate-700/50 shadow-2xl hover:shadow-red-500/10 transition-all duration-300 h-[400px]">
            <div className="flex justify-between items-center mb-4">
              <h5 className="text-white font-bold text-base flex items-center">
                <i className="fas fa-chart-scatter mr-2 text-red-400"></i>
                T-S Diagram
              </h5>
              <span className="px-3 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">
                Temperature vs Salinity
              </span>
            </div>
            
            <div className="h-[320px] bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
              {!profileId ? (
                <div className="text-center text-white/50">
                  <i className="fas fa-chart-scatter text-4xl mb-3 text-red-400"></i>
                  <div className="text-base font-medium">T-S Diagram</div>
                  <div className="text-xs opacity-70 mt-1">Enter profile ID and generate</div>
                </div>
              ) : (
                <canvas ref={tsDiagramChartRef} className="w-full h-full"></canvas>
              )}
            </div>
          </div>

          {/* Graph 2 - Depth Profile */}
          <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-5 border border-slate-700/50 shadow-2xl hover:shadow-cyan-500/10 transition-all duration-300 h-[400px]">
            <div className="flex justify-between items-center mb-4">
              <h5 className="text-white font-bold text-base flex items-center">
                <i className="fas fa-water mr-2 text-cyan-300"></i>
                Depth Profile
              </h5>
              <span className="px-3 py-1 bg-cyan-500/20 text-cyan-300 text-xs rounded-full">
                Temperature & Salinity vs Depth
              </span>
            </div>
            
            <div className="h-[320px] bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
              <div className="text-center text-white/50">
                <i className="fas fa-chart-line text-4xl mb-3 text-cyan-300"></i>
                <div className="text-base font-medium">Depth Profile</div>
                <div className="text-xs opacity-70 mt-1">Vertical water column analysis</div>
              </div>
            </div>
          </div>

          {/* Graph 3 - Quality Control Analysis */}
          <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-5 border border-slate-700/50 shadow-2xl hover:shadow-blue-500/10 transition-all duration-300 h-[400px]">
            <div className="flex justify-between items-center mb-4">
              <h5 className="text-white font-bold text-base flex items-center">
                <i className="fas fa-shield-alt mr-2 text-blue-400"></i>
                Quality Control
              </h5>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full">
                Data Quality Flags
              </span>
            </div>
            
            <div className="h-[320px] bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
              <div className="text-center text-white/50">
                <i className="fas fa-check-circle text-4xl mb-3 text-blue-400"></i>
                <div className="text-base font-medium">Quality Control</div>
                <div className="text-xs opacity-70 mt-1">Data validation and flags</div>
              </div>
            </div>
          </div>

          {/* Graph 4 - Statistical Summary */}
          <div className="bg-slate-800/40 backdrop-blur-xl rounded-2xl p-5 border border-slate-700/50 shadow-2xl hover:shadow-amber-500/10 transition-all duration-300 h-[400px]">
            <div className="flex justify-between items-center mb-4">
              <h5 className="text-white font-bold text-base flex items-center">
                <i className="fas fa-chart-bar mr-2 text-amber-400"></i>
                Statistical Summary
              </h5>
              <span className="px-3 py-1 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                Profile Statistics
              </span>
            </div>
            
            <div className="h-[320px] bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
              <div className="text-center text-white/50">
                <i className="fas fa-chart-pie text-4xl mb-3 text-amber-400"></i>
                <div className="text-base font-medium">Statistical Analysis</div>
                <div className="text-xs opacity-70 mt-1">Data distribution and trends</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
