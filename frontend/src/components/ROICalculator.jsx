import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { IndianRupee, Thermometer, Trees, Clock } from 'lucide-react';

export const ROICalculator = ({ budget }) => {
  const [trees, setTrees] = useState(Math.floor(budget / 500));
  const [species, setSpecies] = useState('neem');

  const speciesData = {
    neem: { cost: 500, cooling: 0.08, growth: 'Fast', maintenance: 50 },
    gulmohar: { cost: 350, cooling: 0.06, growth: 'Medium', maintenance: 40 },
    banyan: { cost: 800, cooling: 0.12, growth: 'Slow', maintenance: 80 },
    peepal: { cost: 600, cooling: 0.10, growth: 'Medium', maintenance: 60 },
    amaltas: { cost: 400, cooling: 0.05, growth: 'Fast', maintenance: 45 }
  };

  const selected = speciesData[species];
  const totalCost = trees * selected.cost;
  const totalCooling = (trees * selected.cooling).toFixed(1);
  const costPerDegree = totalCost / totalCooling;
  const maintenance5yr = trees * selected.maintenance * 5;
  const energySavings = trees * 1500; // INR per tree per year
  const netBenefit5yr = (energySavings * 5) - maintenance5yr - totalCost;

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white">ROI Calculator</h3>

      <div className="grid grid-cols-2 gap-6">
        {/* Controls */}
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400 flex justify-between">
              <span>Number of Trees</span>
              <span className="text-cyan-400">{trees}</span>
            </label>
            <input
              type="range"
              min="10"
              max="1000"
              value={trees}
              onChange={(e) => setTrees(Number(e.target.value))}
              className="w-full mt-2 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-2 block">Tree Species</label>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(speciesData).map(([key, data]) => (
                <button
                  key={key}
                  onClick={() => setSpecies(key)}
                  className={`p-2 rounded-lg text-sm transition-all ${
                    species === key
                      ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 text-cyan-300'
                      : 'bg-white/5 text-gray-400 hover:text-white'
                  }`}
                >
                  <div className="font-medium capitalize">{key}</div>
                  <div className="text-xs opacity-70">₹{data.cost}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <Clock className="w-4 h-4" />
              <span>Species Info</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-gray-400">Growth Rate:</div>
              <div className="text-white">{selected.growth}</div>
              <div className="text-gray-400">Cooling per tree:</div>
              <div className="text-white">{selected.cooling}°C</div>
              <div className="text-gray-400">Yearly maintenance:</div>
              <div className="text-white">₹{selected.maintenance}</div>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="space-y-4">
          <motion.div
            key={totalCost}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="glass-panel p-4 border-l-4 border-cyan-500"
          >
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Total Investment</span>
              <IndianRupee className="w-5 h-5 text-cyan-400" />
            </div>
            <p className="text-3xl font-bold text-white mt-1">₹{totalCost.toLocaleString()}</p>
          </motion.div>

          <motion.div
            key={totalCooling}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="glass-panel p-4 border-l-4 border-heat-cool"
          >
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Expected Cooling</span>
              <Thermometer className="w-5 h-5 text-heat-cool" />
            </div>
            <p className="text-3xl font-bold text-heat-cool mt-1">{totalCooling}°C</p>
          </motion.div>

          <motion.div
            key={costPerDegree}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="glass-panel p-4 border-l-4 border-purple-500"
          >
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Cost per °C Cooled</span>
              <Trees className="w-5 h-5 text-purple-400" />
            </div>
            <p className="text-3xl font-bold text-purple-400 mt-1">₹{Math.round(costPerDegree).toLocaleString()}</p>
          </motion.div>

          <div className={`glass-panel p-4 border-l-4 ${netBenefit5yr > 0 ? 'border-heat-cool' : 'border-heat-danger'}`}>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Net Benefit (5 Years)</span>
              <IndianRupee className={`w-5 h-5 ${netBenefit5yr > 0 ? 'text-heat-cool' : 'text-heat-danger'}`} />
            </div>
            <p className={`text-3xl font-bold mt-1 ${netBenefit5yr > 0 ? 'text-heat-cool' : 'text-heat-danger'}`}>
              ₹{netBenefit5yr.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">Includes energy savings & maintenance costs</p>
          </div>
        </div>
      </div>
    </div>
  );
};
