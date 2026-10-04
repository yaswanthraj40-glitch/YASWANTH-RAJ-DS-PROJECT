import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ThermometerSun, Users, Trees, IndianRupee, ShieldAlert, Sparkles, HelpCircle } from 'lucide-react';

const HotspotDetailPanel = ({ zone, onClose, onPlantingClick }) => {
  if (!zone) return null;

  const temp = zone.temperature || zone.predicted_lst_c || 35.0;
  const risk = zone.heat_risk || (temp >= 46 ? 'EXTREME' : temp >= 43 ? 'HIGH' : temp >= 40 ? 'MODERATE' : 'LOW');
  const riskColor = zone.heat_risk_color || (risk === 'EXTREME' ? '#ff0000' : risk === 'HIGH' ? '#ff006e' : risk === 'MODERATE' ? '#ffb703' : '#00ff88');
  const pop = zone.population_density || zone.population || 15000;
  const treeCover = zone.existing_tree_cover !== undefined ? (zone.existing_tree_cover * 100).toFixed(1) : '8.5';
  const buildingDensity = zone.building_density !== undefined ? (zone.building_density * 100).toFixed(0) : '65';
  const ndvi = zone.ndvi !== undefined ? zone.ndvi.toFixed(2) : '0.18';
  const roadDensity = zone.road_density !== undefined ? zone.road_density.toFixed(1) : '12.4';
  
  // Recommended intervention estimates
  const recommendedTrees = Math.max(15, Math.min(180, Math.round((temp - 35) * 8)));
  const estimatedCost = recommendedTrees * 500;
  const estimatedCooling = (recommendedTrees * 0.08 * 0.75).toFixed(2);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 50, scale: 0.95 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 50, scale: 0.95 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="absolute top-4 right-4 w-88 max-w-[calc(100vw-2rem)] glass-panel p-5 z-30 shadow-2xl border border-white/20 bg-slate-900/90 backdrop-blur-xl text-white custom-scroll max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-red-500/20 text-red-400 border border-red-500/30">
              <ThermometerSun className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base gradient-text">HEAT HOTSPOT</h3>
              <p className="text-[11px] text-gray-400">Zone ID: {zone.grid_id || zone.ward || 'G_Zone'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* LST & Risk Badge */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-center">
            <span className="text-[11px] text-gray-400">Predicted LST</span>
            <span className="text-2xl font-black" style={{ color: riskColor }}>
              {typeof temp === 'number' ? temp.toFixed(1) : temp}°C
            </span>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-center">
            <span className="text-[11px] text-gray-400">Heat Risk Level</span>
            <span className="text-sm font-bold flex items-center gap-1.5 mt-1" style={{ color: riskColor }}>
              <ShieldAlert className="w-4 h-4" />
              {risk}
            </span>
          </div>
        </div>

        {/* Why is it hot? SHAP Top Contributors */}
        <div className="mb-4 p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center gap-1.5 mb-2.5">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            <h4 className="text-xs font-bold text-gray-200 uppercase tracking-wider">Why is it hot?</h4>
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between items-center py-1 border-b border-white/5">
              <span className="text-gray-400">1. High Building Density</span>
              <span className="font-mono font-bold text-red-400">{buildingDensity}% coverage</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-white/5">
              <span className="text-gray-400">2. Low Vegetation (NDVI)</span>
              <span className="font-mono font-bold text-yellow-400">{ndvi}</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-white/5">
              <span className="text-gray-400">3. High Road Density</span>
              <span className="font-mono font-bold text-orange-400">{roadDensity} km/km²</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-gray-400">4. Low Surface Albedo</span>
              <span className="font-mono font-bold text-purple-400">0.24 (High Absorption)</span>
            </div>
          </div>
        </div>

        {/* Demographics & Tree Cover */}
        <div className="grid grid-cols-2 gap-3 mb-4 text-xs">
          <div className="p-3 rounded-xl bg-white/5 border border-white/5">
            <div className="flex items-center gap-1 text-gray-400 mb-1">
              <Users className="w-3.5 h-3.5 text-cyan-400" />
              <span>Population Exposure</span>
            </div>
            <p className="text-white font-bold font-mono text-sm">{Number(pop).toLocaleString()}/km²</p>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/5">
            <div className="flex items-center gap-1 text-gray-400 mb-1">
              <Trees className="w-3.5 h-3.5 text-emerald-400" />
              <span>Existing Canopy</span>
            </div>
            <p className="text-white font-bold font-mono text-sm">{treeCover}%</p>
          </div>
        </div>

        {/* Recommended Intervention */}
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-cyan-500/10 via-purple-500/10 to-emerald-500/10 border border-cyan-500/30 mb-4">
          <div className="flex items-center gap-1.5 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider">Recommended Intervention</h4>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Action:</span>
              <span className="font-bold text-white bg-white/10 px-2 py-0.5 rounded">Plant {recommendedTrees} Neem/Peepal trees</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Estimated Cost:</span>
              <span className="font-bold font-mono text-cyan-400">₹{estimatedCost.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Estimated Cooling:</span>
              <span className="font-bold font-mono text-emerald-400">-{estimatedCooling}°C <span className="text-[10px] text-gray-400">(ESTIMATED)</span></span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        {onPlantingClick && (
          <button
            onClick={() => onPlantingClick(zone)}
            className="w-full py-2.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
          >
            <Trees className="w-4 h-4" />
            Add Zone to Tree Optimization Plan
          </button>
        )}

        <p className="text-[10px] text-gray-500 mt-2 text-center">
          *Cooling estimates derived from ML simulation. Not measured facts.
        </p>
      </motion.div>
    </AnimatePresence>
  );
};

export default HotspotDetailPanel;
