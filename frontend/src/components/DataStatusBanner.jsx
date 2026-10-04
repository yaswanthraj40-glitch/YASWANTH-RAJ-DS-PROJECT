import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, Satellite, Cloud, Brain, AlertTriangle, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

const API = 'http://localhost:8000';

const DataStatusBanner = ({ onStatusLoad }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API}/api/data/status`);
      const data = await resp.json();
      setStatus(data);
      if (onStatusLoad) onStatusLoad(data);
    } catch (err) {
      setStatus({ error: 'Backend offline', global_demo_mode: true });
    } finally {
      setLoading(false);
    }
  };

  const sources = [
    {
      key: 'satellite',
      label: 'Satellite (NDVI/LST)',
      icon: Satellite,
      isDemo: status?.satellite?.is_demo ?? true,
      note: status?.satellite?.note || 'Sentinel-2 + Landsat 9',
    },
    {
      key: 'weather',
      label: 'Weather (Open-Meteo)',
      icon: Cloud,
      isDemo: status?.weather?.is_demo ?? false,
      note: 'Real-time from Open-Meteo API',
    },
    {
      key: 'osm',
      label: 'OSM Buildings/Roads',
      icon: Database,
      isDemo: status?.data?.demo_mode_active ?? true,
      note: 'OpenStreetMap via Overpass API',
    },
    {
      key: 'ml',
      label: 'ML Predictions',
      icon: Brain,
      isDemo: false,
      note: 'XGBoost trained model (real predictions)',
    },
  ];

  const anyDemo = sources.some(s => s.isDemo);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-xs text-yellow-400">
        <RefreshCw className="w-3 h-3 animate-spin" />
        Loading data status...
      </div>
    );
  }

  return (
    <div className="relative">
      <motion.button
        onClick={() => setExpanded(!expanded)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
          anyDemo
            ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/20'
            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
        }`}
        whileHover={{ scale: 1.02 }}
      >
        {anyDemo
          ? <AlertTriangle className="w-3.5 h-3.5" />
          : <CheckCircle className="w-3.5 h-3.5" />}
        {anyDemo ? '⚠ DEMO DATA ACTIVE' : '✅ REAL DATA'}
      </motion.button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            className="absolute top-full right-0 mt-2 w-80 glass-panel p-4 z-50"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-bold text-white">Data Source Status</h4>
              <button onClick={() => setExpanded(false)} className="text-gray-500 hover:text-white text-xs">✕</button>
            </div>

            <div className="space-y-2">
              {sources.map(src => {
                const Icon = src.icon;
                return (
                  <div key={src.key} className="flex items-start gap-3 p-2 rounded-lg bg-white/5">
                    <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${src.isDemo ? 'text-yellow-400' : 'text-emerald-400'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-white text-xs font-medium">{src.label}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                          src.isDemo
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {src.isDemo ? 'DEMO' : 'REAL'}
                        </span>
                      </div>
                      <p className="text-gray-500 text-[10px] mt-0.5 leading-tight">{src.note}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {anyDemo && (
              <div className="mt-3 p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                <p className="text-yellow-400 text-[10px] leading-relaxed">
                  ⚠️ DEMO MODE: Satellite NDVI/LST are simulated (not real measurements).
                  Configure GEE_PROJECT_ID for real satellite data.
                </p>
              </div>
            )}

            <button
              onClick={fetchStatus}
              className="mt-3 w-full flex items-center justify-center gap-2 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 text-xs transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh Status
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DataStatusBanner;
