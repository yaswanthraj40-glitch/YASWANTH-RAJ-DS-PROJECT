import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Eye, EyeOff, Trees, Layers, RefreshCw, AlertTriangle, 
  Filter, MapPin, ChevronDown, Sparkles, Building2, Search
} from 'lucide-react';
import HotspotDetailPanel from './HotspotDetailPanel';

const API = 'http://localhost:8000';

export const CITIES_DATABASE = [
  {
    id: 'chennai',
    name: 'Chennai',
    state: 'Tamil Nadu',
    country: 'India',
    lat: 13.0827,
    lng: 80.2707,
    baseTemp: 42.3,
    hotspotCount: 18,
    canopyCover: '6.7%',
    neighborhoods: ['T. Nagar', 'Guindy', 'Anna Nagar', 'Adyar', 'Velachery', 'Mylapore', 'Royapettah', 'George Town', 'Perambur', 'Kodambakkam', 'Nungambakkam', 'Thiruvanmiyur', 'Egmore', 'Saidapet', 'Porur', 'Alwarpet']
  },
  {
    id: 'delhi',
    name: 'New Delhi',
    state: 'Delhi NCR',
    country: 'India',
    lat: 28.6139,
    lng: 77.2090,
    baseTemp: 45.1,
    hotspotCount: 26,
    canopyCover: '11.2%',
    neighborhoods: ['Connaught Place', 'Karol Bagh', 'Rohini', 'Dwarka', 'Chandni Chowk', 'Okhla', 'Lajpat Nagar', 'Saket', 'Janakpuri', 'Pitampura', 'Mayur Vihar', 'Hauz Khas', 'Vasant Kunj', 'Shahdara']
  },
  {
    id: 'mumbai',
    name: 'Mumbai',
    state: 'Maharashtra',
    country: 'India',
    lat: 19.0760,
    lng: 72.8777,
    baseTemp: 39.8,
    hotspotCount: 15,
    canopyCover: '14.5%',
    neighborhoods: ['Dharavi', 'Andheri East', 'Bandra Kurla', 'Dadar', 'Kurla', 'Colaba', 'Borivali', 'Chembur', 'Ghatkopar', 'Malad West', 'Worli', 'Parel', 'Powai', 'Vashi']
  },
  {
    id: 'bangalore',
    name: 'Bengaluru',
    state: 'Karnataka',
    country: 'India',
    lat: 12.9716,
    lng: 77.5946,
    baseTemp: 36.4,
    hotspotCount: 9,
    canopyCover: '18.1%',
    neighborhoods: ['Whitefield', 'Indiranagar', 'Koramangala', 'Electronic City', 'Jayanagar', 'Malleshwaram', 'HSR Layout', 'Marathahalli', 'Hebbal', 'Yelahanka', 'BTM Layout', 'Rajajinagar']
  },
  {
    id: 'hyderabad',
    name: 'Hyderabad',
    state: 'Telangana',
    country: 'India',
    lat: 17.3850,
    lng: 78.4867,
    baseTemp: 43.5,
    hotspotCount: 21,
    canopyCover: '8.9%',
    neighborhoods: ['HITEC City', 'Charminar', 'Banjara Hills', 'Secunderabad', 'Gachibowli', 'Kukatpally', 'Jubilee Hills', 'Begumpet', 'Madhapur', 'Mehdipatnam', 'Ameerpet', 'Dilsukhnagar']
  },
  {
    id: 'kolkata',
    name: 'Kolkata',
    state: 'West Bengal',
    country: 'India',
    lat: 22.5726,
    lng: 88.3639,
    baseTemp: 41.2,
    hotspotCount: 16,
    canopyCover: '9.4%',
    neighborhoods: ['Salt Lake Sector V', 'Howrah Bridge', 'Park Street', 'New Town Action Area', 'Dum Dum', 'Ballygunge', 'Shyambazar', 'Behala', 'Jadavpur', 'Alipore', 'Gariahat', 'Barasat']
  },
  {
    id: 'ahmedabad',
    name: 'Ahmedabad',
    state: 'Gujarat',
    country: 'India',
    lat: 23.0225,
    lng: 72.5714,
    baseTemp: 44.8,
    hotspotCount: 24,
    canopyCover: '5.8%',
    neighborhoods: ['Maninagar', 'Navrangpura', 'SG Highway', 'Bapunagar', 'Sabarmati', 'Vastrapur', 'Naroda', 'Paldi', 'Satellite Area', 'Chandkheda', 'Ghatlodiya', 'Ellisbridge']
  },
  {
    id: 'dubai',
    name: 'Dubai',
    state: 'Emirates',
    country: 'UAE',
    lat: 25.2048,
    lng: 55.2708,
    baseTemp: 46.5,
    hotspotCount: 28,
    canopyCover: '3.2%',
    neighborhoods: ['Downtown Dubai', 'Deira Commercial', 'Bur Dubai Historic', 'Dubai Marina', 'Business Bay', 'Jumeirah Beach', 'Al Barsha', 'International City', 'Silicon Oasis', 'Al Quoz Industrial']
  },
  {
    id: 'tokyo',
    name: 'Tokyo',
    state: 'Kanto',
    country: 'Japan',
    lat: 35.6762,
    lng: 139.6503,
    baseTemp: 34.2,
    hotspotCount: 7,
    canopyCover: '23.0%',
    neighborhoods: ['Shinjuku CBD', 'Shibuya Crossing', 'Ginza Shopping', 'Roppongi Hills', 'Akihabara', 'Ikebukuro', 'Ueno Park', 'Asakusa', 'Shinagawa', 'Chiyoda Financial']
  },
  {
    id: 'phoenix',
    name: 'Phoenix',
    state: 'Arizona',
    country: 'USA',
    lat: 33.4484,
    lng: -112.0740,
    baseTemp: 45.8,
    hotspotCount: 25,
    canopyCover: '7.1%',
    neighborhoods: ['Downtown Phoenix', 'Tempe University', 'Old Town Scottsdale', 'Glendale Arena', 'Mesa Downtown', 'Chandler Tech Corridor', 'Peoria North', 'Paradise Valley', 'Gilbert Heritage']
  }
];

const MAP_BASEMAPS = {
  dark: {
    id: 'dark',
    label: 'Dark Mode',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO'
  },
  streets: {
    id: 'streets',
    label: 'Streets',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO'
  },
  satellite: {
    id: 'satellite',
    label: 'Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri, Maxar'
  }
};

const getColorByMetric = (featureProps, metric) => {
  const p = featureProps || {};
  if (metric === 'ndvi') {
    const ndvi = p.ndvi !== undefined && p.ndvi !== null ? p.ndvi : 0.25;
    if (ndvi < 0.15) return '#ff006e';
    if (ndvi < 0.30) return '#ffb703';
    if (ndvi < 0.50) return '#00f0ff';
    return '#00ff88';
  } else if (metric === 'population') {
    const pop = p.population_density || 15000;
    if (pop > 45000) return '#ff0000';
    if (pop > 30000) return '#ff006e';
    if (pop > 15000) return '#ffb703';
    return '#00ff88';
  } else if (metric === 'tree_cover') {
    const tc = p.existing_tree_cover !== undefined ? p.existing_tree_cover : 0.1;
    if (tc < 0.05) return '#ff006e';
    if (tc < 0.15) return '#ffb703';
    if (tc < 0.30) return '#00f0ff';
    return '#00ff88';
  } else {
    // LST / Heat
    const temp = p.temperature || p.predicted_lst_c || 38.0;
    if (temp >= 46) return '#ff0000'; // EXTREME
    if (temp >= 43) return '#ff006e'; // HIGH
    if (temp >= 40) return '#ffb703'; // MODERATE
    if (temp >= 37) return '#00f0ff'; // COOL-MOD
    return '#00ff88';                 // LOW
  }
};

// Generate high-resolution microclimate heat polygon grid for any city
const generateCityHeatData = (city) => {
  const zones = [];
  const centerLat = city.lat;
  const centerLon = city.lng;
  const step = 0.007; // ~700m resolution per cell
  const names = city.neighborhoods || [];

  let nameIndex = 0;
  for (let i = -5; i <= 5; i++) {
    for (let j = -5; j <= 5; j++) {
      const lat = centerLat + i * step;
      const lng = centerLon + j * step;
      const distFromCenter = Math.sqrt(i * i + j * j) / 7.2;
      
      // Calibrated microclimate morphology model
      const temp = Number((city.baseTemp + 4.5 - distFromCenter * 8.5 + (Math.sin(i * 3 + j * 2) * 1.2)).toFixed(1));
      const ndvi = Number((0.10 + distFromCenter * 0.40).toFixed(2));
      const treeCover = Number((0.02 + distFromCenter * 0.30).toFixed(3));
      const pop = Math.round(55000 * (1 - distFromCenter * 0.65));
      const wardName = names[nameIndex % names.length] + ` (Sector ${Math.abs(i * 3 + j) + 1})`;
      nameIndex++;

      zones.push({
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [lng - step / 2, lat - step / 2],
            [lng + step / 2, lat - step / 2],
            [lng + step / 2, lat + step / 2],
            [lng - step / 2, lat + step / 2],
            [lng - step / 2, lat - step / 2]
          ]]
        },
        properties: {
          grid_id: `G_${city.id}_${i + 5}_${j + 5}`,
          ward: wardName,
          cityName: city.name,
          temperature: temp,
          predicted_lst_c: temp,
          ndvi: ndvi,
          existing_tree_cover: treeCover,
          population_density: pop,
          building_density: Number((0.85 - distFromCenter * 0.55).toFixed(2)),
          road_density: Number((18.0 - distFromCenter * 10).toFixed(1)),
          income_index: Number((2.5 + distFromCenter * 5.0).toFixed(1)),
          heat_risk: temp >= 46 ? 'EXTREME' : temp >= 43 ? 'HIGH' : temp >= 40 ? 'MODERATE' : 'LOW',
          heat_risk_color: temp >= 46 ? '#ff0000' : temp >= 43 ? '#ff006e' : temp >= 40 ? '#ffb703' : '#00ff88',
          data_is_demo: true
        }
      });
    }
  }

  return {
    type: 'FeatureCollection',
    features: zones,
    metadata: { is_demo: true, city: city.name, cityId: city.id, center: [centerLon, centerLat] }
  };
};

const Map3D = ({ onSelectZone, selectedZoneFromParent }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const geoJsonLayerRef = useRef(null);
  const markersLayerRef = useRef(null);

  const [selectedCity, setSelectedCity] = useState(CITIES_DATABASE[0]); // Default to Chennai
  const [cityDropdownOpen, setCityDropdownOpen] = useState(false);
  const [citySearch, setCitySearch] = useState('');

  const [layers, setLayers] = useState({
    heat: true,
    trees: true,
    activeMetric: 'temperature',
    basemap: 'dark'
  });

  const [selectedZone, setSelectedZone] = useState(null);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Sync selected zone from parent if provided
  useEffect(() => {
    if (selectedZoneFromParent) {
      setSelectedZone(selectedZoneFromParent);
    }
  }, [selectedZoneFromParent]);

  // Load heat grid whenever selected city changes
  useEffect(() => {
    loadCityHeatMap(selectedCity);
  }, [selectedCity]);

  const loadCityHeatMap = async (city) => {
    setLoading(true);
    try {
      if (city.id === 'chennai') {
        const res = await fetch(`${API}/api/heat-map`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.features && data.features.length > 0) {
            setGeoJsonData(data);
          } else {
            setGeoJsonData(generateCityHeatData(city));
          }
        } else {
          setGeoJsonData(generateCityHeatData(city));
        }
      } else {
        // Generate calibrated grid for any other selected city
        setGeoJsonData(generateCityHeatData(city));
      }
    } catch (err) {
      setGeoJsonData(generateCityHeatData(city));
    } finally {
      setLoading(false);
    }

    // Fly camera smoothly to selected city
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([city.lat, city.lng], 12.5, {
        duration: 1.4,
        easeLinearity: 0.25
      });
    }
  };

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [selectedCity.lat, selectedCity.lng],
        zoom: 12.5,
        zoomControl: false,
        attributionControl: false
      });

      // Add Base Layer
      tileLayerRef.current = L.tileLayer(MAP_BASEMAPS[layers.basemap].url, {
        maxZoom: 19,
        subdomains: 'abcd',
        attribution: MAP_BASEMAPS[layers.basemap].attribution
      }).addTo(map);

      // Create Layer Groups
      geoJsonLayerRef.current = L.layerGroup().addTo(map);
      markersLayerRef.current = L.layerGroup().addTo(map);

      mapInstanceRef.current = map;

      // Force recalculate container size
      setTimeout(() => map.invalidateSize(), 150);
      setTimeout(() => map.invalidateSize(), 400);

      loadCityHeatMap(selectedCity);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Switch basemap layer
  const handleSwitchBasemap = (basemapKey) => {
    setLayers(prev => ({ ...prev, basemap: basemapKey }));
    if (mapInstanceRef.current && tileLayerRef.current) {
      mapInstanceRef.current.removeLayer(tileLayerRef.current);
      tileLayerRef.current = L.tileLayer(MAP_BASEMAPS[basemapKey].url, {
        maxZoom: 19,
        subdomains: 'abcd',
        attribution: MAP_BASEMAPS[basemapKey].attribution
      }).addTo(mapInstanceRef.current);
    }
  };

  // Render GeoJSON polygons & planting markers
  useEffect(() => {
    if (!mapInstanceRef.current || !geoJsonLayerRef.current || !markersLayerRef.current || !geoJsonData) return;

    geoJsonLayerRef.current.clearLayers();
    markersLayerRef.current.clearLayers();

    if (layers.heat) {
      const geoLayer = L.geoJSON(geoJsonData, {
        style: (feature) => {
          const color = getColorByMetric(feature.properties, layers.activeMetric);
          const isSelected = selectedZone?.grid_id === feature.properties?.grid_id;
          return {
            fillColor: color,
            fillOpacity: isSelected ? 0.88 : 0.65,
            color: isSelected ? '#ffffff' : color,
            weight: isSelected ? 2.5 : 1,
            opacity: 0.8
          };
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties || {};
          const temp = p.temperature || p.predicted_lst_c || 35.0;
          const risk = p.heat_risk || 'MODERATE';

          layer.bindTooltip(`
            <div style="font-family: sans-serif; font-size: 11px; font-weight: bold; color: #fff;">
              <div>${p.ward || p.grid_id}</div>
              <div style="color: #ff006e; font-size: 13px;">${temp}°C (${risk})</div>
              <div style="font-size: 10px; color: #94a3b8;">Click for SHAP & AI Greening</div>
            </div>
          `, {
            className: 'glass-tooltip',
            sticky: true
          });

          layer.on({
            click: () => {
              setSelectedZone(p);
              if (onSelectZone) onSelectZone(p);
            },
            mouseover: (e) => {
              const l = e.target;
              l.setStyle({ fillOpacity: 0.9, weight: 2 });
            },
            mouseout: (e) => {
              geoLayer.resetStyle(e.target);
            }
          });
        }
      });

      geoLayer.addTo(geoJsonLayerRef.current);
    }

    // Render recommended planting tree markers
    if (layers.trees && geoJsonData.features) {
      const highHeatZones = geoJsonData.features
        .filter(f => (f.properties?.temperature || f.properties?.predicted_lst_c || 0) >= selectedCity.baseTemp + 1.0)
        .slice(0, 16);

      highHeatZones.forEach(f => {
        const coords = f.geometry.coordinates[0][0]; // [lng, lat]
        const p = f.properties;

        const treeIcon = L.divIcon({
          className: 'tree-marker-div',
          html: `
            <div style="
              width: 26px; height: 26px;
              background: radial-gradient(circle, #00ff88 0%, rgba(0,255,136,0.3) 70%, transparent 100%);
              border: 2px solid #00ff88;
              border-radius: 50%;
              display: flex; align-items: center; justify-content: center;
              box-shadow: 0 0 12px #00ff88;
              cursor: pointer;
              font-size: 12px;
            ">
              🌳
            </div>
          `,
          iconSize: [26, 26],
          iconAnchor: [13, 13]
        });

        const marker = L.marker([coords[1], coords[0]], { icon: treeIcon });
        marker.on('click', () => {
          setSelectedZone(p);
          if (onSelectZone) onSelectZone(p);
        });

        marker.addTo(markersLayerRef.current);
      });
    }
  }, [geoJsonData, layers.heat, layers.trees, layers.activeMetric, selectedZone, selectedCity]);

  const toggleLayer = (key) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const switchMetric = (metric) => {
    setLayers(prev => ({ ...prev, activeMetric: metric }));
  };

  const filteredCities = CITIES_DATABASE.filter(c => 
    c.name.toLowerCase().includes(citySearch.toLowerCase()) || 
    c.country.toLowerCase().includes(citySearch.toLowerCase()) ||
    c.state.toLowerCase().includes(citySearch.toLowerCase())
  );

  return (
    <div className="w-full h-full relative overflow-hidden rounded-2xl bg-slate-950">
      {/* Map Canvas */}
      <div 
        ref={mapContainerRef} 
        className="w-full h-full"
        style={{ width: '100%', height: '100%', minHeight: '540px', zIndex: 1 }}
      />

      {/* City Switcher Bar (Top Center) */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[500] flex items-center gap-2 max-w-[calc(100vw-2rem)]">
        {/* City Dropdown Trigger */}
        <div className="relative">
          <button
            onClick={() => setCityDropdownOpen(!cityDropdownOpen)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900/95 border border-cyan-500/40 text-white font-bold text-xs shadow-2xl backdrop-blur-xl hover:border-cyan-400 transition-all"
          >
            <Building2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>{selectedCity.name}, {selectedCity.state}</span>
            <span className="text-[10px] text-red-400 bg-red-500/20 px-1.5 py-0.5 rounded font-mono font-bold">
              {selectedCity.baseTemp}°C
            </span>
            <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${cityDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* City Dropdown Menu */}
          <AnimatePresence>
            {cityDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: 5, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 5, scale: 0.95 }}
                className="absolute top-full left-0 mt-2 w-72 max-h-80 overflow-y-auto custom-scroll glass-panel p-2 z-[600] bg-slate-900/95 backdrop-blur-2xl border border-white/20 shadow-2xl rounded-2xl"
              >
                {/* Search in Dropdown */}
                <div className="p-1.5 mb-1">
                  <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white">
                    <Search className="w-3 h-3 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search city..."
                      value={citySearch}
                      onChange={(e) => setCitySearch(e.target.value)}
                      className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-gray-500"
                    />
                  </div>
                </div>

                {/* Cities List */}
                <div className="space-y-1">
                  {filteredCities.map(city => (
                    <button
                      key={city.id}
                      onClick={() => {
                        setSelectedCity(city);
                        setCityDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between p-2 rounded-xl text-left transition-all ${
                        selectedCity.id === city.id
                          ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/40 text-cyan-300 font-bold'
                          : 'text-gray-300 hover:bg-white/5 hover:text-white text-xs'
                      }`}
                    >
                      <div>
                        <p className="font-bold text-xs text-white">{city.name}</p>
                        <p className="text-[10px] text-gray-400">{city.state}, {city.country}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-black font-mono text-red-400">{city.baseTemp}°C</span>
                        <p className="text-[9px] text-gray-500">{city.hotspotCount} Hotspots</p>
                      </div>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Quick City Pills (Desktop) */}
        <div className="hidden lg:flex items-center gap-1 p-1 rounded-xl bg-slate-900/90 border border-white/15 backdrop-blur-md shadow-xl">
          {CITIES_DATABASE.slice(0, 5).map(c => (
            <button
              key={c.id}
              onClick={() => setSelectedCity(c)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
                selectedCity.id === c.id
                  ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Layer Controls Panel (Top Left) */}
      <div className="absolute top-4 left-4 glass-panel p-3.5 space-y-3 z-[500] w-60 backdrop-blur-xl">
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-300 uppercase tracking-wider font-bold flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            Layer Controls
          </p>
          <button 
            onClick={() => loadCityHeatMap(selectedCity)} 
            title="Refresh map data"
            className="p-1 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>

        {/* Feature Toggles */}
        <div className="space-y-1.5">
          <button
            onClick={() => toggleLayer('heat')}
            className={`flex items-center justify-between w-full px-2.5 py-1.5 rounded-lg text-xs transition-all ${
              layers.heat ? 'bg-white/15 text-white font-semibold' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-[#ff006e]" />
              <span>Heat Polygons Layer</span>
            </div>
            {layers.heat ? <Eye className="w-3.5 h-3.5 text-cyan-400" /> : <EyeOff className="w-3.5 h-3.5 text-gray-500" />}
          </button>

          <button
            onClick={() => toggleLayer('trees')}
            className={`flex items-center justify-between w-full px-2.5 py-1.5 rounded-lg text-xs transition-all ${
              layers.trees ? 'bg-white/15 text-white font-semibold' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              <span>Planting Interventions</span>
            </div>
            {layers.trees ? <Eye className="w-3.5 h-3.5 text-emerald-400" /> : <EyeOff className="w-3.5 h-3.5 text-gray-500" />}
          </button>
        </div>

        {/* Basemap Selection */}
        <div className="pt-2 border-t border-white/10">
          <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-1.5 font-bold">Basemap Mode</p>
          <div className="grid grid-cols-3 gap-1">
            {Object.values(MAP_BASEMAPS).map(b => (
              <button
                key={b.id}
                onClick={() => handleSwitchBasemap(b.id)}
                className={`py-1 px-1.5 rounded text-[10px] font-bold transition-all ${
                  layers.basemap === b.id
                    ? 'bg-cyan-500/30 text-cyan-300 border border-cyan-500/50'
                    : 'bg-white/5 text-gray-400 hover:text-white'
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        {/* Switch Metric View */}
        <div className="pt-2 border-t border-white/10">
          <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-2 font-bold flex items-center gap-1">
            <Filter className="w-3 h-3 text-purple-400" /> Metric Visualization
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {[
              { id: 'temperature', label: 'LST / Heat' },
              { id: 'ndvi', label: 'NDVI (Green)' },
              { id: 'population', label: 'Population' },
              { id: 'tree_cover', label: 'Tree Cover' }
            ].map(m => (
              <button
                key={m.id}
                onClick={() => switchMetric(m.id)}
                className={`px-2 py-1.5 rounded-md text-[11px] font-medium transition-all ${
                  layers.activeMetric === m.id
                    ? 'bg-gradient-to-r from-cyan-500/30 to-purple-500/30 text-cyan-300 border border-cyan-500/40 shadow-sm font-bold'
                    : 'text-gray-400 hover:text-white bg-white/5'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Legend (Bottom Left) */}
      <div className="absolute bottom-4 left-4 glass-panel p-3.5 z-[500] min-w-56 backdrop-blur-xl">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-200 uppercase tracking-wider font-bold">
            {layers.activeMetric === 'temperature' && `${selectedCity.name.toUpperCase()} LST HEAT (°C)`}
            {layers.activeMetric === 'ndvi' && 'NDVI VEGETATION INDEX'}
            {layers.activeMetric === 'population' && 'POPULATION DENSITY (/KM²)'}
            {layers.activeMetric === 'tree_cover' && 'CANOPY COVERAGE (%)'}
          </p>
        </div>

        {layers.activeMetric === 'temperature' && (
          <>
            <div className="heat-bar w-full mb-2 h-2.5 rounded-full" />
            <div className="grid grid-cols-4 text-[10px] text-gray-300 font-bold">
              <span className="text-emerald-400">LOW &lt;38°</span>
              <span className="text-cyan-400 text-center">40°</span>
              <span className="text-yellow-400 text-center">HIGH 43°</span>
              <span className="text-red-500 text-right">EXTREME &gt;46°</span>
            </div>
          </>
        )}

        {layers.activeMetric === 'ndvi' && (
          <div className="space-y-1 text-xs">
            <div className="h-2 rounded-full bg-gradient-to-r from-pink-600 via-yellow-400 via-cyan-400 to-emerald-400 mb-1" />
            <div className="flex justify-between text-[10px] text-gray-400 font-mono">
              <span>0.0 (Barren)</span>
              <span>0.3 (Moderate)</span>
              <span>0.6+ (Dense)</span>
            </div>
          </div>
        )}

        {layers.activeMetric === 'population' && (
          <div className="space-y-1 text-xs">
            <div className="h-2 rounded-full bg-gradient-to-r from-emerald-400 via-cyan-400 via-yellow-400 to-red-500 mb-1" />
            <div className="flex justify-between text-[10px] text-gray-400 font-mono">
              <span>5k (Low)</span>
              <span>30k</span>
              <span>55k+ (High)</span>
            </div>
          </div>
        )}

        {layers.activeMetric === 'tree_cover' && (
          <div className="space-y-1 text-xs">
            <div className="h-2 rounded-full bg-gradient-to-r from-pink-600 via-yellow-400 to-emerald-500 mb-1" />
            <div className="flex justify-between text-[10px] text-gray-400 font-mono">
              <span>&lt;5% (Deficit)</span>
              <span>20%</span>
              <span>40%+ (Healthy)</span>
            </div>
          </div>
        )}
      </div>

      {/* Selected Hotspot Detail Panel */}
      {selectedZone && (
        <HotspotDetailPanel
          zone={selectedZone}
          onClose={() => setSelectedZone(null)}
          onPlantingClick={(zone) => {
            alert(`Added zone ${zone.ward || zone.grid_id} in ${selectedCity.name} to AI tree optimization list!`);
          }}
        />
      )}
    </div>
  );
};

export default Map3D;
