import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Search, Layers, Plus, Minus, ThermometerSun, 
  MapPin, ShieldAlert, Trees, Globe, X
} from 'lucide-react';

const CITIES = [
  { id: 'chennai', name: 'Chennai', country: 'India', lat: 13.0827, lng: 80.2707, temp: 42.3, risk: 'EXTREME', riskColor: '#ff0000', pop: '11.5M', treeCover: '6.7%', ndvi: 0.18, uhiSeverity: 'Severe (+5.8°C)' },
  { id: 'delhi', name: 'New Delhi', country: 'India', lat: 28.6139, lng: 77.2090, temp: 45.1, risk: 'EXTREME', riskColor: '#ff0000', pop: '32.9M', treeCover: '11.2%', ndvi: 0.22, uhiSeverity: 'Extreme (+6.5°C)' },
  { id: 'mumbai', name: 'Mumbai', country: 'India', lat: 19.0760, lng: 72.8777, temp: 39.8, risk: 'HIGH', riskColor: '#ff006e', pop: '21.3M', treeCover: '14.5%', ndvi: 0.28, uhiSeverity: 'High (+4.2°C)' },
  { id: 'bangalore', name: 'Bengaluru', country: 'India', lat: 12.9716, lng: 77.5946, temp: 36.4, risk: 'MODERATE', riskColor: '#ffb703', pop: '13.6M', treeCover: '18.1%', ndvi: 0.38, uhiSeverity: 'Moderate (+3.1°C)' },
  { id: 'hyderabad', name: 'Hyderabad', country: 'India', lat: 17.3850, lng: 78.4867, temp: 43.5, risk: 'HIGH', riskColor: '#ff006e', pop: '10.8M', treeCover: '8.9%', ndvi: 0.21, uhiSeverity: 'High (+5.0°C)' },
  { id: 'kolkata', name: 'Kolkata', country: 'India', lat: 22.5726, lng: 88.3639, temp: 41.2, risk: 'HIGH', riskColor: '#ff006e', pop: '15.3M', treeCover: '9.4%', ndvi: 0.24, uhiSeverity: 'High (+4.6°C)' },
  { id: 'ahmedabad', name: 'Ahmedabad', country: 'India', lat: 23.0225, lng: 72.5714, temp: 44.8, risk: 'EXTREME', riskColor: '#ff0000', pop: '8.6M', treeCover: '5.8%', ndvi: 0.15, uhiSeverity: 'Extreme (+6.1°C)' },
  { id: 'tokyo', name: 'Tokyo', country: 'Japan', lat: 35.6762, lng: 139.6503, temp: 34.2, risk: 'MODERATE', riskColor: '#ffb703', pop: '37.4M', treeCover: '23.0%', ndvi: 0.42, uhiSeverity: 'Moderate (+2.8°C)' },
  { id: 'dubai', name: 'Dubai', country: 'UAE', lat: 25.2048, lng: 55.2708, temp: 46.5, risk: 'EXTREME', riskColor: '#ff0000', pop: '3.5M', treeCover: '3.2%', ndvi: 0.08, uhiSeverity: 'Severe (+5.5°C)' },
  { id: 'singapore', name: 'Singapore', country: 'Singapore', lat: 1.3521, lng: 103.8198, temp: 32.8, risk: 'LOW', riskColor: '#00ff88', pop: '5.9M', treeCover: '47.0%', ndvi: 0.65, uhiSeverity: 'Mitigated (+1.4°C)' },
  { id: 'london', name: 'London', country: 'UK', lat: 51.5074, lng: -0.1278, temp: 28.5, risk: 'LOW', riskColor: '#00ff88', pop: '9.0M', treeCover: '33.0%', ndvi: 0.52, uhiSeverity: 'Low (+1.9°C)' },
  { id: 'phoenix', name: 'Phoenix', country: 'USA', lat: 33.4484, lng: -112.0740, temp: 45.8, risk: 'EXTREME', riskColor: '#ff0000', pop: '4.8M', treeCover: '7.1%', ndvi: 0.12, uhiSeverity: 'Extreme (+6.2°C)' },
];

const MAP_LAYERS = {
  streets: {
    id: 'streets',
    label: 'Default',
    icon: '🗺️',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
  },
  satellite: {
    id: 'satellite',
    label: 'Satellite',
    icon: '🛰️',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri, Maxar, Earthstar Geographics'
  },
  dark: {
    id: 'dark',
    label: 'Dark',
    icon: '🌙',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
  },
  osm: {
    id: 'osm',
    label: 'Terrain',
    icon: '⛰️',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors'
  }
};

const Globe3D = ({ onCitySelect }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const markersLayerRef = useRef(null);
  const circlesLayerRef = useRef(null);

  const [selectedCity, setSelectedCity] = useState(CITIES[0]);
  const [activeLayerKey, setActiveLayerKey] = useState('streets');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL');

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Prevent duplicate initialization in React StrictMode
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [13.0827, 80.2707],
        zoom: 5,
        zoomControl: false,
        attributionControl: false
      });

      // Add base tile layer
      tileLayerRef.current = L.tileLayer(MAP_LAYERS[activeLayerKey].url, {
        maxZoom: 19,
        subdomains: 'abcd',
        attribution: MAP_LAYERS[activeLayerKey].attribution
      }).addTo(map);

      // Create layer groups for markers and heat glow circles
      circlesLayerRef.current = L.layerGroup().addTo(map);
      markersLayerRef.current = L.layerGroup().addTo(map);

      mapInstanceRef.current = map;

      // Force recalculation of container size after mounting
      setTimeout(() => map.invalidateSize(), 100);
      setTimeout(() => map.invalidateSize(), 300);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Tile Layer when basemap is changed
  const handleSwitchBasemap = (layerKey) => {
    setActiveLayerKey(layerKey);
    if (mapInstanceRef.current && tileLayerRef.current) {
      mapInstanceRef.current.removeLayer(tileLayerRef.current);
      tileLayerRef.current = L.tileLayer(MAP_LAYERS[layerKey].url, {
        maxZoom: 19,
        subdomains: 'abcd',
        attribution: MAP_LAYERS[layerKey].attribution
      }).addTo(mapInstanceRef.current);
    }
  };

  // Re-render pins and heat circles whenever filters or selected city changes
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current || !circlesLayerRef.current) return;

    markersLayerRef.current.clearLayers();
    circlesLayerRef.current.clearLayers();

    const filtered = CITIES.filter(c => {
      const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) || c.country.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesRisk = filterRisk === 'ALL' || c.risk === filterRisk;
      return matchesSearch && matchesRisk;
    });

    filtered.forEach(city => {
      const isSelected = selectedCity?.id === city.id;

      // 1. Add Radiant Heat Circle
      const heatRadius = Math.max(35000, (city.temp - 25) * 4500);
      const circle = L.circle([city.lat, city.lng], {
        radius: heatRadius,
        color: city.riskColor,
        fillColor: city.riskColor,
        fillOpacity: isSelected ? 0.35 : 0.22,
        weight: isSelected ? 2 : 1,
        dashArray: isSelected ? '4, 4' : null
      });
      circle.addTo(circlesLayerRef.current);

      // 2. Add Google Maps-style custom HTML marker
      const customIcon = L.divIcon({
        className: 'custom-google-pin',
        html: `
          <div style="
            display: flex;
            align-items: center;
            background: ${isSelected ? '#0f172a' : '#ffffff'};
            color: ${isSelected ? '#ffffff' : '#1e293b'};
            border: 2px solid ${city.riskColor};
            padding: 3px 8px;
            border-radius: 20px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
            transform: ${isSelected ? 'scale(1.15)' : 'scale(1)'};
            transition: transform 0.2s ease;
            cursor: pointer;
          ">
            <span style="
              width: 7px; height: 7px;
              background: ${city.riskColor};
              border-radius: 50%;
              margin-right: 5px;
              display: inline-block;
              box-shadow: 0 0 6px ${city.riskColor};
            "></span>
            <span>${city.name}</span>
            <span style="
              margin-left: 4px;
              background: ${city.riskColor}25;
              color: ${city.riskColor};
              padding: 1px 4px;
              border-radius: 6px;
              font-size: 10px;
              font-weight: 800;
            ">${city.temp}°C</span>
          </div>
        `,
        iconSize: [110, 30],
        iconAnchor: [55, 15]
      });

      const marker = L.marker([city.lat, city.lng], { icon: customIcon });
      marker.on('click', () => {
        handleSelectCity(city);
      });

      marker.addTo(markersLayerRef.current);
    });
  }, [selectedCity, searchQuery, filterRisk, activeLayerKey]);

  const handleSelectCity = (city) => {
    setSelectedCity(city);
    if (onCitySelect) onCitySelect(city);

    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([city.lat, city.lng], 7, {
        duration: 1.2,
        easeLinearity: 0.25
      });
    }
  };

  const handleZoom = (delta) => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.setZoom(mapInstanceRef.current.getZoom() + delta);
  };

  const handleResetLocation = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.flyTo([13.0827, 80.2707], 5, {
      duration: 1.2
    });
  };

  return (
    <div className="w-full h-[620px] relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-slate-900">
      {/* Leaflet Map Canvas */}
      <div 
        ref={mapContainerRef} 
        className="w-full h-full" 
        style={{ width: '100%', height: '100%', minHeight: '620px', zIndex: 1 }}
      />

      {/* Google Maps Search & Filter Bar (Top Left) */}
      <div className="absolute top-4 left-4 z-[500] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
        {/* Search Box */}
        <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-white/95 text-slate-900 shadow-2xl backdrop-blur-md border border-slate-200">
          <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <input
            type="text"
            placeholder="Search city (e.g. Chennai, Delhi, Tokyo)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-transparent text-xs font-semibold text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="text-xs text-slate-400 hover:text-slate-700">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Risk Filter Chips */}
        <div className="flex items-center gap-1.5 p-1.5 rounded-xl bg-slate-900/90 border border-white/15 backdrop-blur-md shadow-xl">
          {['ALL', 'EXTREME', 'HIGH', 'MODERATE'].map(risk => (
            <button
              key={risk}
              onClick={() => setFilterRisk(risk)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                filterRisk === risk
                  ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {risk}
            </button>
          ))}
        </div>
      </div>

      {/* Google Maps Layer Switcher (Top Right) */}
      <div className="absolute top-4 right-4 z-[500] flex items-center gap-1 p-1 bg-white/95 rounded-xl shadow-2xl border border-slate-200 backdrop-blur-md">
        {Object.values(MAP_LAYERS).map(layer => (
          <button
            key={layer.id}
            onClick={() => handleSwitchBasemap(layer.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeLayerKey === layer.id
                ? 'bg-slate-900 text-white shadow'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>{layer.icon}</span>
            <span className="hidden sm:inline">{layer.label}</span>
          </button>
        ))}
      </div>

      {/* Google Maps Zoom & Recenter Controls (Bottom Right) */}
      <div className="absolute bottom-6 right-4 z-[500] flex flex-col gap-2">
        <button
          onClick={handleResetLocation}
          title="Reset to India View"
          className="w-9 h-9 rounded-xl bg-white text-slate-800 shadow-2xl border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition-colors font-bold"
        >
          <Globe className="w-4 h-4 text-cyan-600" />
        </button>
        <div className="flex flex-col rounded-xl bg-white text-slate-800 shadow-2xl border border-slate-200 overflow-hidden">
          <button
            onClick={() => handleZoom(1)}
            title="Zoom in"
            className="w-9 h-9 flex items-center justify-center hover:bg-slate-100 border-b border-slate-100 transition-colors text-slate-700 font-bold"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleZoom(-1)}
            title="Zoom out"
            className="w-9 h-9 flex items-center justify-center hover:bg-slate-100 transition-colors text-slate-700 font-bold"
          >
            <Minus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Google Maps Selected City Inspection Drawer (Bottom Left) */}
      <AnimatePresence>
        {selectedCity && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            className="absolute bottom-6 left-4 z-[500] w-96 max-w-[calc(100vw-2rem)] glass-panel p-4.5 bg-slate-900/95 backdrop-blur-2xl border border-white/20 shadow-2xl text-white rounded-2xl"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-black text-white">{selectedCity.name}</h3>
                  <span className="text-xs text-gray-400 font-medium">({selectedCity.country})</span>
                </div>
                <p className="text-[11px] text-gray-400 flex items-center gap-1 mt-0.5">
                  <MapPin className="w-3 h-3 text-cyan-400" />
                  {selectedCity.lat.toFixed(2)}°N, {selectedCity.lng.toFixed(2)}°E
                </p>
              </div>
              <div
                className="px-2.5 py-1 rounded-full text-xs font-black border"
                style={{
                  backgroundColor: `${selectedCity.riskColor}20`,
                  borderColor: `${selectedCity.riskColor}50`,
                  color: selectedCity.riskColor
                }}
              >
                {selectedCity.risk} RISK
              </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                <span className="text-[10px] text-gray-400">Surface LST</span>
                <p className="text-base font-black font-mono" style={{ color: selectedCity.riskColor }}>
                  {selectedCity.temp}°C
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                <span className="text-[10px] text-gray-400">Canopy Cover</span>
                <p className="text-base font-black font-mono text-emerald-400">{selectedCity.treeCover}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                <span className="text-[10px] text-gray-400">UHI Severity</span>
                <p className="text-[11px] font-bold text-yellow-400 mt-1 leading-tight">{selectedCity.uhiSeverity}</p>
              </div>
            </div>

            {/* Population & NDVI */}
            <div className="flex items-center justify-between text-[11px] text-gray-400 px-1 mb-3">
              <span>Population: <b className="text-white">{selectedCity.pop}</b></span>
              <span>NDVI: <b className="text-cyan-300">{selectedCity.ndvi}</b></span>
            </div>

            {/* Action */}
            <button
              onClick={() => {
                alert(`Loaded ${selectedCity.name} microclimate model!`);
              }}
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2"
            >
              <Trees className="w-3.5 h-3.5" />
              Analyze {selectedCity.name} Microclimate
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Globe3D;
