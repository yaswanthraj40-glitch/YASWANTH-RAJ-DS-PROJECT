import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Satellite, Brain, Scale, Map, BarChart3, MessageSquare, ChevronRight } from 'lucide-react';
import TiltCard3D from './TiltCard3D';

const features = [
  {
    id: 'satellite',
    icon: Satellite,
    title: 'Satellite Intelligence',
    subtitle: 'Landsat 9 + Sentinel-2',
    color: '#00f0ff',
    description: 'Real-time thermal imaging from space captures surface temperatures across every ward. 30m resolution with cloud-gap interpolation.',
    stats: [
      { label: 'Resolution', value: '30m' },
      { label: 'Bands', value: '11' },
      { label: 'Refresh', value: '16 days' }
    ]
  },
  {
    id: 'ml',
    icon: Brain,
    title: 'XGBoost Predictor',
    subtitle: '9-Dimensional Analysis',
    color: '#a855f7',
    description: 'Machine learning model predicts heat from building density, roads, vegetation, population, elevation, and 4 more features.',
    stats: [
      { label: 'Accuracy', value: '85%' },
      { label: 'Features', value: '9' },
      { label: 'MAE', value: '1.2°C' }
    ]
  },
  {
    id: 'equity',
    icon: Scale,
    title: 'Equity Engine',
    subtitle: 'Social Justice First',
    color: '#ff006e',
    description: 'Prioritizes low-income neighborhoods with the formula: Heat × Population × IncomeVulnerability ÷ Cost.',
    stats: [
      { label: 'Weight', value: '40%' },
      { label: 'Wards', value: '200' },
      { label: 'Impact', value: '45K+' }
    ]
  },
  {
    id: '3dmap',
    icon: Map,
    title: '3D Visualization',
    subtitle: 'Interactive Heat Maps',
    color: '#ffb703',
    description: 'Extruded polygons rise from the map like 3D bars. Click any zone to see ward details, temperature, and tree recommendations.',
    stats: [
      { label: 'Polygons', value: '50+' },
      { label: 'Buildings', value: '3D' },
      { label: 'Layers', value: '4' }
    ]
  },
  {
    id: 'analytics',
    icon: BarChart3,
    title: 'Smart Analytics',
    subtitle: 'ROI & Impact Tracking',
    color: '#00ff88',
    description: 'Real-time cost-per-degree-cooled calculator. Track energy savings, CO₂ absorption, and lives saved over 5 years.',
    stats: [
      { label: 'ROI', value: '₹2.3L' },
      { label: 'Energy', value: '1.2M' },
      { label: 'CO₂', value: '450T' }
    ]
  },
  {
    id: 'chatbot',
    icon: MessageSquare,
    title: 'AI Assistant',
    subtitle: 'Ask Anything',
    color: '#f472b6',
    description: 'Not preloaded answers — real AI that understands context. Ask about heat science, your city, tree species, or anything else.',
    stats: [
      { label: 'Topics', value: '∞' },
      { label: 'Response', value: '<2s' },
      { label: 'Model', value: 'GPT-4o' }
    ]
  }
];

const FeatureShowcase3D = () => {
  const [activeFeature, setActiveFeature] = useState(0);

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold gradient-text">System Architecture</h3>
          <p className="text-gray-400 text-sm mt-1">6 core modules working together</p>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Feature List */}
        <div className="col-span-4 space-y-2">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            const isActive = i === activeFeature;
            return (
              <motion.button
                key={feature.id}
                onClick={() => setActiveFeature(i)}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all text-left ${
                  isActive
                    ? 'bg-white/10 border border-white/20'
                    : 'hover:bg-white/5'
                }`}
              >
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${feature.color}20` }}
                >
                  <Icon className="w-5 h-5" style={{ color: feature.color }} />
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${isActive ? 'text-white' : 'text-gray-400'}`}>
                    {feature.title}
                  </p>
                  <p className="text-xs text-gray-500">{feature.subtitle}</p>
                </div>
                <ChevronRight className={`w-4 h-4 transition-colors ${isActive ? 'text-cyan-400' : 'text-gray-600'}`} />
              </motion.button>
            );
          })}
        </div>

        {/* Feature Detail */}
        <div className="col-span-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeFeature}
              initial={{ opacity: 0, rotateY: -15, x: -20 }}
              animate={{ opacity: 1, rotateY: 0, x: 0 }}
              exit={{ opacity: 0, rotateY: 15, x: 20 }}
              transition={{ duration: 0.4 }}
              style={{ perspective: '1000px' }}
            >
              <TiltCard3D scale={1.01}>
                <div className="glass-panel p-6 h-full border-2" style={{ borderColor: `${features[activeFeature].color}30` }}>
                  <div className="flex items-start gap-4 mb-4">
                    <div 
                      className="w-14 h-14 rounded-2xl flex items-center justify-center"
                      style={{ backgroundColor: `${features[activeFeature].color}20` }}
                    >
                      {React.createElement(features[activeFeature].icon, {
                        className: "w-7 h-7",
                        style: { color: features[activeFeature].color }
                      })}
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-white">{features[activeFeature].title}</h4>
                      <p className="text-sm" style={{ color: features[activeFeature].color }}>
                        {features[activeFeature].subtitle}
                      </p>
                    </div>
                  </div>

                  <p className="text-gray-300 leading-relaxed mb-6">
                    {features[activeFeature].description}
                  </p>

                  <div className="grid grid-cols-3 gap-4">
                    {features[activeFeature].stats.map((stat, i) => (
                      <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="p-4 rounded-xl bg-white/5 text-center"
                      >
                        <p className="text-2xl font-bold" style={{ color: features[activeFeature].color }}>
                          {stat.value}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">{stat.label}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </TiltCard3D>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default FeatureShowcase3D;
