import { useEffect, useState } from 'react';
import { OceanDataResponse } from '../types/ocean';

export function useOceanData(query: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OceanDataResponse>({});

  useEffect(() => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    // Simulate API call with mock data for demo
    const mockResponse = generateMockResponse(query);
    
    // Simulate network delay
    setTimeout(() => {
      setData(mockResponse);
      setLoading(false);
    }, 1000 + Math.random() * 1000);
    
  }, [query]);

  return { ...data, loading, error };
}

function generateMockResponse(query: string): OceanDataResponse {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes('temperature') && lowerQuery.includes('profile')) {
    return {
      message: "Temperature profile from Arabian Sea showing typical thermocline structure at 65°E, 20°N.",
      viz_spec: {
        viz_type: 'profile_plot',
        title: 'Temperature Profile - Arabian Sea',
        mark: 'line',
        encoding: {
          x: { field: 'temperature_c', type: 'quantitative', title: 'Temperature (°C)' },
          y: { field: 'depth_m', type: 'quantitative', title: 'Depth (m)' }
        },
        fields_required: ['temperature_c', 'depth_m']
      },
      rows: generateProfileData()
    };
  }
  
  if (lowerQuery.includes('salinity') && lowerQuery.includes('time')) {
    return {
      message: "Salinity time series from Argo float 2901623 showing seasonal variation in the Arabian Sea.",
      viz_spec: {
        viz_type: 'time_series_point',
        title: 'Salinity Time Series - Arabian Sea',
        mark: 'line',
        encoding: {
          x: { field: 'timestamp', type: 'temporal', title: 'Date' },
          y: { field: 'salinity_psu', type: 'quantitative', title: 'Salinity (PSU)' }
        },
        fields_required: ['timestamp', 'salinity_psu']
      },
      rows: generateTimeSeriesData()
    };
  }
  
  if (lowerQuery.includes('t-s') || lowerQuery.includes('ts diagram')) {
    return {
      message: "T-S diagram showing water mass characteristics in the Arabian Sea. Note the high salinity Persian Gulf Water signature.",
      viz_spec: {
        viz_type: 'ts_diagram',
        title: 'T-S Diagram - Arabian Sea Water Masses',
        mark: 'point',
        encoding: {
          x: { field: 'salinity_psu', type: 'quantitative', title: 'Salinity (PSU)' },
          y: { field: 'temperature_c', type: 'quantitative', title: 'Temperature (°C)' },
          color: { field: 'depth_m', type: 'quantitative', title: 'Depth (m)' }
        },
        fields_required: ['salinity_psu', 'temperature_c', 'depth_m']
      },
      rows: generateTSData()
    };
  }
  
  if (lowerQuery.includes('trajectory') || lowerQuery.includes('float')) {
    return {
      message: "Argo float trajectory showing drift pattern in Arabian Sea circulation over 2 years.",
      viz_spec: {
        viz_type: 'trajectory_map',
        title: 'Argo Float Trajectory - Arabian Sea',
        mark: 'point',
        encoding: {
          x: { field: 'lon', type: 'quantitative', title: 'Longitude' },
          y: { field: 'lat', type: 'quantitative', title: 'Latitude' },
          color: { field: 'timestamp', type: 'temporal', title: 'Date' }
        },
        fields_required: ['lon', 'lat', 'timestamp']
      },
      rows: generateTrajectoryData()
    };
  }
  
  // Default response
  return {
    message: "Here's a sample temperature profile from the Arabian Sea. Try asking about 'salinity time series', 'T-S diagram', or 'float trajectory'.",
    viz_spec: {
      viz_type: 'profile_plot',
      title: 'Temperature Profile - Arabian Sea',
      mark: 'line',
      encoding: {
        x: { field: 'temperature_c', type: 'quantitative', title: 'Temperature (°C)' },
        y: { field: 'depth_m', type: 'quantitative', title: 'Depth (m)' }
      },
      fields_required: ['temperature_c', 'depth_m']
    },
    rows: generateProfileData()
  };
}

function generateProfileData() {
  const data = [];
  for (let depth = 0; depth <= 2000; depth += 50) {
    let temp;
    if (depth < 50) temp = 28 - depth * 0.1;
    else if (depth < 200) temp = 23 - (depth - 50) * 0.08;
    else if (depth < 1000) temp = 11 - (depth - 200) * 0.008;
    else temp = 4.5 - (depth - 1000) * 0.001;
    
    data.push({
      depth_m: depth,
      temperature_c: Math.round(temp * 10) / 10
    });
  }
  return data;
}

function generateTimeSeriesData() {
  const data = [];
  const startDate = new Date('2023-01-01');
  for (let i = 0; i < 365; i += 10) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const seasonal = Math.sin((i / 365) * 2 * Math.PI) * 0.3;
    const salinity = 36.5 + seasonal + (Math.random() - 0.5) * 0.2;
    
    data.push({
      timestamp: date.toISOString().split('T')[0],
      salinity_psu: Math.round(salinity * 100) / 100
    });
  }
  return data;
}

function generateTSData() {
  const data = [];
  for (let i = 0; i < 100; i++) {
    const depth = Math.random() * 2000;
    let temp, sal;
    
    if (depth < 100) {
      temp = 26 + Math.random() * 3;
      sal = 36.0 + Math.random() * 0.8;
    } else if (depth < 500) {
      temp = 15 + Math.random() * 8;
      sal = 35.5 + Math.random() * 1.0;
    } else {
      temp = 4 + Math.random() * 6;
      sal = 34.7 + Math.random() * 0.6;
    }
    
    data.push({
      temperature_c: Math.round(temp * 10) / 10,
      salinity_psu: Math.round(sal * 100) / 100,
      depth_m: Math.round(depth)
    });
  }
  return data;
}

function generateTrajectoryData() {
  const data = [];
  let lat = 20.0;
  let lon = 65.0;
  const startDate = new Date('2023-01-01');
  
  for (let i = 0; i < 100; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i * 7);
    
    // Simulate drift
    lat += (Math.random() - 0.5) * 0.2;
    lon += (Math.random() - 0.5) * 0.3;
    
    data.push({
      lat: Math.round(lat * 1000) / 1000,
      lon: Math.round(lon * 1000) / 1000,
      timestamp: date.toISOString().split('T')[0],
      float_id: '2901623'
    });
  }
  return data;
}