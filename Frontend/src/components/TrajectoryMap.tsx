import { useEffect, useRef } from 'react';
import { useLeafletMap } from '../hooks/useLeafletMap';
import L from 'leaflet';

interface TrajectoryMapProps {
  containerId: string;
  theme: string;
  floatId: number | null;
  height?: string;
}

export function TrajectoryMap({ containerId, theme, floatId, height = '100%' }: TrajectoryMapProps) {
  const { map, isReady, switchTheme } = useLeafletMap(containerId, {
    center: [0, 80],
    zoom: 2,
    theme: 'natgeo',
  });

  const trajectoryLineRef = useRef<L.Polyline | null>(null);
  const markersRef = useRef<L.Marker[]>([]);

  // Update theme when prop changes
  useEffect(() => {
    if (isReady) {
      switchTheme(theme);
    }
  }, [theme, isReady, switchTheme]);

  // Load trajectory when floatId changes
  useEffect(() => {
    if (!map || !isReady || !floatId) return;

    const loadTrajectory = async (id: number) => {
      if (!map) return;

      try {
        // Clear previous trajectory
        if (trajectoryLineRef.current) {
          map.removeLayer(trajectoryLineRef.current);
        }
        markersRef.current.forEach((marker) => map.removeLayer(marker));
        markersRef.current = [];

        // Fetch trajectory data from API
        const response = await fetch(`http://127.0.0.1:8000/float/${id}/trajectory`);
        const trajectoryData = await response.json();

        if (trajectoryData && trajectoryData.length > 0) {
          // Create polyline from trajectory points
          const latlngs: [number, number][] = trajectoryData.map((point: { lat: number; lon: number; date: string }) => [
            point.lat,
            point.lon,
          ]);

          const polyline = L.polyline(latlngs, {
            color: '#10B981',
            weight: 3,
            opacity: 0.7,
          }).addTo(map);

          trajectoryLineRef.current = polyline;

          // Add markers for start and end points
          const startPoint = trajectoryData[0];
          const endPoint = trajectoryData[trajectoryData.length - 1];

          const startMarker = L.marker([startPoint.lat, startPoint.lon], {
            icon: L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
              iconSize: [20, 33],
              iconAnchor: [10, 33],
              popupAnchor: [0, -28],
              shadowSize: [33, 33],
            }),
          })
            .bindPopup(`<b>Start</b><br>${startPoint.date}`)
            .addTo(map);

          const endMarker = L.marker([endPoint.lat, endPoint.lon], {
            icon: L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
              iconSize: [20, 33],
              iconAnchor: [10, 33],
              popupAnchor: [0, -28],
              shadowSize: [33, 33],
            }),
          })
            .bindPopup(`<b>Current</b><br>${endPoint.date}`)
            .addTo(map);

          markersRef.current = [startMarker, endMarker];

          // Fit map to trajectory bounds
          map.fitBounds(polyline.getBounds(), { padding: [20, 20] });
        }
      } catch (error) {
        console.error('Error loading trajectory:', error);
        // Add mock trajectory for demonstration
        addMockTrajectory();
      }
    };

    const addMockTrajectory = () => {
      if (!map) return;

      // Clear previous trajectory
      if (trajectoryLineRef.current) {
        map.removeLayer(trajectoryLineRef.current);
      }
      markersRef.current.forEach((marker) => map.removeLayer(marker));
      markersRef.current = [];

      const mockTrajectory = [
        { lat: 12.5, lon: 74.2, date: 'Jan 22' },
        { lat: 12.6, lon: 74.5, date: 'Jan 29' },
        { lat: 12.7, lon: 74.8, date: 'Feb 05' },
        { lat: 12.9, lon: 75.0, date: 'Feb 12' },
        { lat: 13.1, lon: 75.1, date: 'Feb 19' },
        { lat: 13.3, lon: 75.0, date: 'Feb 26' },
      ];

      const latlngs: [number, number][] = mockTrajectory.map((point) => [point.lat, point.lon]);

      const polyline = L.polyline(latlngs, {
        color: '#10B981',
        weight: 3,
        opacity: 0.7,
      }).addTo(map);

      trajectoryLineRef.current = polyline;

      // Add start marker
      const startMarker = L.marker([mockTrajectory[0].lat, mockTrajectory[0].lon], {
        icon: L.icon({
          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
          iconSize: [20, 33],
          iconAnchor: [10, 33],
          popupAnchor: [0, -28],
          shadowSize: [33, 33],
        }),
      })
        .bindPopup(`<b>Start</b><br>${mockTrajectory[0].date}`)
        .addTo(map);

      // Add end marker
      const lastIdx = mockTrajectory.length - 1;
      const endMarker = L.marker([mockTrajectory[lastIdx].lat, mockTrajectory[lastIdx].lon], {
        icon: L.icon({
          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
          iconSize: [20, 33],
          iconAnchor: [10, 33],
          popupAnchor: [0, -28],
          shadowSize: [33, 33],
        }),
      })
        .bindPopup(`<b>Current</b><br>${mockTrajectory[lastIdx].date}`)
        .addTo(map);

      markersRef.current = [startMarker, endMarker];

      map.fitBounds(polyline.getBounds(), { padding: [20, 20] });
    };

    loadTrajectory(floatId);
  }, [map, isReady, floatId]);

  return (
    <div
      id={containerId}
      style={{
        height,
        width: '100%',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.12)',
        overflow: 'hidden',
      }}
    />
  );
}
