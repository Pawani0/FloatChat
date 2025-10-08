import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';

export interface MapTheme {
  url: string;
  attribution?: string;
  maxZoom: number;
  subdomains?: string;
}

export const mapThemes: Record<string, MapTheme> = {
  ocean: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
    attribution: '',
    maxZoom: 13,
  },
  natgeo: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
    attribution: '',
    maxZoom: 16,
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '',
    maxZoom: 19,
  },
  dark: {
    url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
    attribution: '',
    maxZoom: 20,
  },
  light: {
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '',
    maxZoom: 19,
    subdomains: 'abcd',
  },
};

export interface UseLeafletMapOptions {
  center?: [number, number];
  zoom?: number;
  theme?: string;
}

export function useLeafletMap(
  containerId: string,
  options: UseLeafletMapOptions = {}
) {
  const { center = [0, 80], zoom = 3, theme = 'natgeo' } = options;
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const container = document.getElementById(containerId);
    if (!container || mapRef.current) return;

    try {
      // Initialize map
      const map = L.map(containerId).setView(center, zoom);
      mapRef.current = map;

      // Add tile layer
      const themeConfig = mapThemes[theme];
      const tileLayer = L.tileLayer(themeConfig.url, {
        attribution: themeConfig.attribution,
        maxZoom: themeConfig.maxZoom,
        subdomains: themeConfig.subdomains,
      });
      tileLayer.addTo(map);
      tileLayerRef.current = tileLayer;

      setIsReady(true);
    } catch (error) {
      console.error('Error initializing map:', error);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        tileLayerRef.current = null;
        setIsReady(false);
      }
    };
  }, [containerId, center, zoom, theme]);

  const switchTheme = (newTheme: string) => {
    if (!mapRef.current || !tileLayerRef.current) return;

    const themeConfig = mapThemes[newTheme];
    if (!themeConfig) return;

    mapRef.current.removeLayer(tileLayerRef.current);
    const newTileLayer = L.tileLayer(themeConfig.url, {
      attribution: themeConfig.attribution,
      maxZoom: themeConfig.maxZoom,
      subdomains: themeConfig.subdomains,
    });
    newTileLayer.addTo(mapRef.current);
    tileLayerRef.current = newTileLayer;
  };

  return {
    map: mapRef.current,
    isReady,
    switchTheme,
  };
}
