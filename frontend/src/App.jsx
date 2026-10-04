import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ThermometerSun, Trees, TrendingDown, Map, BarChart3, MessageCircle, 
  X, Menu, Globe, Layers, Zap, ChevronDown, Sparkles, CheckCircle 
} from 'lucide-react';

import ParticleBackground from './components/ParticleBackground';
import Globe3D from './components/Globe3D';
import Map3D from './components/Map3D';
import Dashboard from './components/Dashboard';
import StatsCards3D from './components/StatsCards3D';
import Chatbot from './components/Chatbot';
import BeforeAfter3D from './components/BeforeAfter3D';
import WardCarousel3D from './components/WardCarousel3D';
import HeatCylinderChart from './components/HeatCylinderChart';
import FeatureShowcase3D from './components/FeatureShowcase3D';
import DataStatusBanner from './components/DataStatusBanner';

const API = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('map'); // default to Heat Map view
  const [showChat, setShowChat] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [scrolled, setScrolled] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState(null);

  const [cityData, setCityData] = useState({
    cityName: 'Chennai',
    avgTemp: 41.0,
    hotZones: 446,
    budget: 900000,
    equityPriority: 50,
    recommendedTrees: 1875,
    expectedCooling: 2.4,
    peopleBenefited: 72.1,
    waterSaved: 4.0,
    co2Absorbed: 780,
    energySaved: 2.1
  });

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Fetch summary stats on startup
  useEffect(() => {
    fetch(`${API}/api/impact-summary`)
      .then(r => r.json())
      .then(data => {
        if (data && data.avg_lst_c) {
          setCityData(prev => ({
            ...prev,
            avgTemp: data.avg_lst_c || prev.avgTemp,
            hotZones: data.hotspot_count || prev.hotZones,
          }));
        }
      })
      .catch(() => {});
  }, []);

  // Live slider change handlers
  const handleBudgetChange = (newBudget) => {
    const trees = Math.round(newBudget / 480);
    const cooling = Number((trees * 0.0018 + (cityData.equityPriority / 100) * 0.6).toFixed(1));
    const people = Number(((trees * 38.5 * (1 + cityData.equityPriority / 100)) / 1000).toFixed(1));
    const water = Number((trees * 2.15 / 1000).toFixed(1));
    const co2 = Math.round(trees * 0.42);
    const energy = Number((trees * 1.15 / 1000).toFixed(1));

    setCityData(prev => ({
      ...prev,
      budget: newBudget,
      recommendedTrees: trees,
      expectedCooling: cooling,
      peopleBenefited: people,
      waterSaved: water,
      co2Absorbed: co2,
      energySaved: energy
    }));
  };

  const handleEquityChange = (newEquity) => {
    const trees = cityData.recommendedTrees || Math.round(cityData.budget / 480);
    const cooling = Number((trees * 0.0018 + (newEquity / 100) * 0.6).toFixed(1));
    const people = Number(((trees * 38.5 * (1 + newEquity / 100)) / 1000).toFixed(1));

    setCityData(prev => ({
      ...prev,
      equityPriority: newEquity,
      expectedCooling: cooling,
      peopleBenefited: people
    }));
  };

  // Call Optimizer when "Generate Plan" is clicked
  const handleGeneratePlan = async () => {
    setOptimizing(true);
    try {
      const resp = await fetch(`${API}/api/optimization`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget: cityData.budget,
          max_trees: Math.round(cityData.budget / 400),
          equity_weight: cityData.equityPriority / 100
        })
      });
      const result = await resp.json();
      setOptimizationResult(result);
      if (result && result.total_trees) {
        const trees = result.total_trees;
        const cooling = result.summary?.expected_avg_cooling_c || Number((trees * 0.0022).toFixed(1));
        const people = Number(((trees * 42.0 * (1 + cityData.equityPriority / 100)) / 1000).toFixed(1));
        const water = Number((trees * 2.2 / 1000).toFixed(1));
        const co2 = Math.round(trees * 0.45);
        const energy = Number((trees * 1.2 / 1000).toFixed(1));

        setCityData(prev => ({
          ...prev,
          recommendedTrees: trees,
          expectedCooling: cooling,
          peopleBenefited: people,
          waterSaved: water,
          co2Absorbed: co2,
          energySaved: energy
        }));
      }
    } catch (err) {
      console.warn('Optimizer API offline, using calculation fallback:', err);
      handleBudgetChange(cityData.budget);
    } finally {
      setOptimizing(false);
    }
  };

  const navItems = [
    { id: 'map', label: '3D Heat Map', icon: Map },
    { id: 'dashboard', label: 'Analytics Hub', icon: BarChart3 },
    { id: 'globe', label: 'Global Monitor', icon: Globe },
  ];

  return (
    <div className="min-h-screen w-full bg-slate-950 relative overflow-hidden">
      {/* Particle Background */}
      <ParticleBackground />

      {/* Main Layout */}
      <div className="relative z-10 flex h-screen">

        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-80 glass-panel m-4 mr-0 flex flex-col z-20 overflow-y-auto custom-scroll"
            >
              {/* Logo */}
              <div className="p-5 border-b border-white/10">
                <motion.div 
                  className="flex items-center gap-3"
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-cyan-500/30 pulse-glow-3d">
                    <ThermometerSun className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-xl font-black gradient-text glow-text">CoolRoute</h1>
                    <p className="text-[10px] text-gray-400 tracking-wider font-bold">URBAN HEAT MITIGATION AI</p>
                  </div>
                </motion.div>
              </div>

              {/* Navigation */}
              <nav className="flex-1 p-4 space-y-1.5">
                {navItems.map((item) => (
                  <motion.button
                    key={item.id}
                    whileHover={{ x: 6, scale: 1.01 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl transition-all ${
                      activeTab === item.id
                        ? 'bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-pink-500/20 border border-cyan-500/30 text-cyan-300 shadow-lg shadow-cyan-500/10 font-bold'
                        : 'text-gray-400 hover:text-white hover:bg-white/5 font-medium'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="text-sm">{item.label}</span>
                    {activeTab === item.id && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400"
                      />
                    )}
                  </motion.button>
                ))}

                {/* Configuration / Optimization Controls */}
                <div className="pt-4 border-t border-white/10 mt-3">
                  <div className="flex items-center justify-between mb-3 px-3">
                    <p className="text-[11px] text-gray-400 uppercase tracking-wider font-bold">Optimization Engine</p>
                    <span className="text-[10px] text-cyan-400 font-mono">XGBoost + Greedy</span>
                  </div>

                  <div className="space-y-4 px-3">
                    {/* Budget Slider */}
                    <div>
                      <label className="text-xs text-gray-300 flex justify-between items-center mb-1.5">
                        <span className="flex items-center gap-1.5">
                          <Zap className="w-3.5 h-3.5 text-yellow-400" />
                          Budget Allocation
                        </span>
                        <span className="text-cyan-400 font-bold font-mono">₹{(cityData.budget / 100000).toFixed(1)}L</span>
                      </label>
                      <input
                        type="range"
                        min="100000"
                        max="2000000"
                        step="50000"
                        value={cityData.budget}
                        onChange={(e) => handleBudgetChange(Number(e.target.value))}
                        className="w-full"
                      />
                      <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                        <span>₹1L</span>
                        <span>₹20L</span>
                      </div>
                    </div>

                    {/* Equity Slider */}
                    <div>
                      <label className="text-xs text-gray-300 flex justify-between items-center mb-1.5">
                        <span className="flex items-center gap-1.5">
                          <Layers className="w-3.5 h-3.5 text-pink-400" />
                          Equity Priority
                        </span>
                        <span className="text-pink-400 font-bold">{cityData.equityPriority}%</span>
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={cityData.equityPriority}
                        onChange={(e) => handleEquityChange(Number(e.target.value))}
                        className="w-full accent-pink-500"
                      />
                      <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                        <span>Efficiency</span>
                        <span>Equitable</span>
                      </div>
                    </div>

                    {/* Generate Button */}
                    <motion.button
                      whileHover={{ scale: 1.02, boxShadow: '0 0 25px rgba(0, 240, 255, 0.35)' }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleGeneratePlan}
                      disabled={optimizing}
                      className="w-full py-3 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 rounded-xl font-bold text-white text-xs shadow-xl shadow-cyan-500/25 relative overflow-hidden group flex items-center justify-center gap-2"
                    >
                      {optimizing ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Solving Optimization...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          <span>Generate Planting Plan</span>
                        </>
                      )}
                    </motion.button>

                    {/* Optimization Feedback */}
                    {optimizationResult && (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-300 space-y-1"
                      >
                        <div className="flex items-center gap-1 font-bold">
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Optimization Complete</span>
                        </div>
                        <p className="text-gray-300">
                          Allocated <b>{optimizationResult.total_trees}</b> trees across <b>{optimizationResult.zones_selected}</b> zones.
                        </p>
                        <p className="text-gray-400 text-[10px]">
                          Avg cooling: -{optimizationResult.summary?.expected_avg_cooling_c}°C (ESTIMATED)
                        </p>
                      </motion.div>
                    )}
                  </div>
                </div>
              </nav>

              {/* Sidebar Footer */}
              <div className="p-3.5 border-t border-white/10">
                <div className="flex items-center gap-2 text-[11px] text-gray-400">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Production Ready • v2.0 Hackathon Build</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Workspace Area */}
        <div className="flex-1 flex flex-col m-4 gap-4 overflow-hidden">
          {/* Top Bar */}
          <motion.div 
            className={`glass-panel px-4 py-3 flex items-center justify-between transition-all ${scrolled ? 'shadow-lg shadow-cyan-500/10' : ''}`}
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
          >
            <div className="flex items-center gap-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
              >
                {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </motion.button>
              <div>
                <h2 className="text-base font-bold text-white">
                  {activeTab === 'map' && '3D Urban Heat & Intervention Simulator'}
                  {activeTab === 'dashboard' && 'AI Analytics & SHAP Explainability'}
                  {activeTab === 'globe' && 'Global Climate Resilience Monitor'}
                </h2>
                <p className="text-[11px] text-gray-400">
                  {activeTab === 'map' && 'Interactive extruded heat polygons with ML-driven intervention plans'}
                  {activeTab === 'dashboard' && 'XGBoost feature attributions, model accuracy & temporal curves'}
                  {activeTab === 'globe' && 'Global urban heat anomaly tracking and climate metrics'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Real / Demo Data Status Banner */}
              <DataStatusBanner />

              {/* Surface Temp Badge */}
              <motion.div 
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500/30 text-xs"
                whileHover={{ scale: 1.02 }}
              >
                <ThermometerSun className="w-4 h-4 text-red-400 animate-pulse" />
                <span className="text-red-400 font-bold font-mono">{cityData.avgTemp}°C</span>
                <span className="text-gray-400 text-[10px]">Avg LST</span>
              </motion.div>

              {/* Chatbot Toggle Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowChat(!showChat)}
                className="p-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 text-white shadow-lg shadow-cyan-500/30 pulse-glow-3d relative"
              >
                <MessageCircle className="w-4 h-4" />
                {!showChat && (
                  <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full animate-ping" />
                )}
              </motion.button>
            </div>
          </motion.div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto custom-scroll pr-1">
            <AnimatePresence mode="wait">

              {/* MAP VIEW */}
              {activeTab === 'map' && (
                <motion.div
                  key="map"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {/* 3D Mapbox Component */}
                  <div className="glass-panel overflow-hidden h-[540px]">
                    <Map3D />
                  </div>

                  {/* Before / After Simulation Component */}
                  <BeforeAfter3D />

                  {/* Ward Carousel */}
                  <WardCarousel3D />
                </motion.div>
              )}

              {/* DASHBOARD VIEW */}
              {activeTab === 'dashboard' && (
                <motion.div
                  key="dashboard"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {/* Stats Cards */}
                  <StatsCards3D data={cityData} />

                  {/* 3D Cylinder Chart */}
                  <div className="glass-panel p-6">
                    <h3 className="text-lg font-bold gradient-text mb-3">3D Thermal Topography</h3>
                    <HeatCylinderChart />
                  </div>

                  {/* Comprehensive Analytics Dashboard */}
                  <div className="glass-panel p-6">
                    <Dashboard data={cityData} />
                  </div>
                </motion.div>
              )}

              {/* GLOBE VIEW */}
              {activeTab === 'globe' && (
                <motion.div
                  key="globe"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {/* 2D Global Map View */}
                  <div className="glass-panel overflow-hidden h-[620px] relative">
                    <Globe3D />
                  </div>

                  {/* Stats Row */}
                  <StatsCards3D data={cityData} />

                  {/* Feature Showcase */}
                  <FeatureShowcase3D />
                </motion.div>
              )}

            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Floating Chatbot Window */}
      <AnimatePresence>
        {showChat && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 50 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <Chatbot onClose={() => setShowChat(false)} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
