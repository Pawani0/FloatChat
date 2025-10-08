import { useEffect, useRef } from 'react';
import { useLeafletMap } from '../hooks/useLeafletMap';
import L from 'leaflet';

// Fix for default marker icons in Leaflet with Vite
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface MapComponentProps {
  containerId: string;
  theme: string;
  onFloatClick?: (floatId: number) => void;
  height?: string;
}

export function MapComponent({ containerId, theme, onFloatClick, height = '420px' }: MapComponentProps) {
  const { map, isReady, switchTheme } = useLeafletMap(containerId, {
    center: [0, 80],
    zoom: 3,
    theme: 'natgeo',
  });
  
  const floatMarkersRef = useRef<L.LayerGroup | null>(null);
  const searchedMarkersRef = useRef<L.LayerGroup | null>(null);

  // Update theme when prop changes
  useEffect(() => {
    if (isReady) {
      switchTheme(theme);
    }
  }, [theme, isReady, switchTheme]);

  // Initialize marker layers
  useEffect(() => {
    if (!map || !isReady) return;

    floatMarkersRef.current = L.layerGroup().addTo(map);
    searchedMarkersRef.current = L.layerGroup().addTo(map);

    // Load float data from API
    const loadFloatMarkers = async () => {
      if (!map || !floatMarkersRef.current) return;

      try {
        // Try to fetch from backend API
        const response = await fetch('http://34.93.9.34:8000/api/dashboard/floats');
        const floats = await response.json();

        floats.forEach((float: { id: number; lat: number; lon: number; data_mode: string }) => {
          const isRealtime = float.data_mode === 'R';
          
          // Create custom icon based on data mode
          const markerIcon = isRealtime
            ? L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
              })
            : L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
              });

          const marker = L.marker([float.lat, float.lon], {
            icon: markerIcon,
            title: `Float ${float.id}`,
          });

          marker.bindPopup(`
            <div style="font-family: Arial, sans-serif;">
              <h6 style="margin: 0 0 10px 0; color: ${isRealtime ? '#10B981' : '#EAB308'};">
                ${isRealtime ? '🟢 Real-time Float' : '🟡 Other Float'}
              </h6>
              <b>Float ID:</b> ${float.id}<br>
              <b>Latitude:</b> ${float.lat.toFixed(4)}<br>
              <b>Longitude:</b> ${float.lon.toFixed(4)}<br>
              <b>Data Mode:</b> ${float.data_mode || 'N/A'}<br>
              <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee;">
                <button onclick="window.viewFloatData(${float.id})" 
                        style="background: ${isRealtime ? '#10B981' : '#EAB308'}; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px; cursor: pointer;">
                  📊 View Data
                </button>
              </div>
            </div>
          `);

          marker.on('click', () => {
            if (onFloatClick) {
              onFloatClick(float.id);
            }
          });

          marker.addTo(floatMarkersRef.current!);
        });
      } catch (error) {
        console.error('Error loading floats:', error);
        // Add mock data for demonstration
        addMockFloatMarkers();
      }
    };

    const addMockFloatMarkers = () => {
      if (!map || !floatMarkersRef.current) return;

      const mockFloats = [
        { id: 2902264, lat: 12.5, lon: 74.2, data_mode: 'R' },
        { id: 2902265, lat: 8.3, lon: 77.1, data_mode: 'A' },
        { id: 2902266, lat: 15.2, lon: 68.5, data_mode: 'R' },
        { id: 2902267, lat: 5.8, lon: 80.3, data_mode: 'D' },
        { id: 2902268, lat: 18.1, lon: 72.8, data_mode: 'R' },
      ];

      mockFloats.forEach((float) => {
        const isRealtime = float.data_mode === 'R';
        const markerIcon = isRealtime
          ? L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
              shadowSize: [41, 41],
            })
          : L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
              shadowSize: [41, 41],
            });

        const marker = L.marker([float.lat, float.lon], {
          icon: markerIcon,
          title: `Float ${float.id}`,
        });

        marker.bindPopup(`
          <div style="font-family: Arial, sans-serif;">
            <h6 style="margin: 0 0 10px 0; color: ${isRealtime ? '#10B981' : '#EAB308'};">
              ${isRealtime ? '🟢 Real-time Float' : '🟡 Other Float'}
            </h6>
            <b>Float ID:</b> ${float.id}<br>
            <b>Latitude:</b> ${float.lat.toFixed(4)}<br>
            <b>Longitude:</b> ${float.lon.toFixed(4)}<br>
            <b>Data Mode:</b> ${float.data_mode}<br>
          </div>
        `);

        marker.on('click', () => {
          if (onFloatClick) {
            onFloatClick(float.id);
          }
        });

        marker.addTo(floatMarkersRef.current!);
      });
    };

    loadFloatMarkers();

    return () => {
      if (floatMarkersRef.current) {
        floatMarkersRef.current.clearLayers();
      }
      if (searchedMarkersRef.current) {
        searchedMarkersRef.current.clearLayers();
      }
    };
  }, [map, isReady, onFloatClick]);

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
