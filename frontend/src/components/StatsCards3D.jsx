import React from 'react';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import TiltCard3D from './TiltCard3D';
import { ThermometerSun, Trees, TrendingDown, AlertTriangle, IndianRupee, Users, Droplets, Wind } from 'lucide-react';

const StatsCards3D = ({ data }) => {
  const trees = data.recommendedTrees || Math.round((data.budget || 500000) / 480);
  const equity = data.equityPriority !== undefined ? data.equityPriority : 50;

  // Dynamically derive all impact indicators from budget, trees, and equity inputs
  const peopleVal = data.peopleBenefited !== undefined 
    ? data.peopleBenefited 
    : Number(((trees * 38.5 * (1 + equity / 100)) / 1000).toFixed(1));

  const waterVal = data.waterSaved !== undefined 
    ? data.waterSaved 
    : Number((trees * 2.15 / 1000).toFixed(1));

  const co2Val = data.co2Absorbed !== undefined 
    ? data.co2Absorbed 
    : Math.round(trees * 0.42);

  const energyVal = data.energySaved !== undefined 
    ? data.energySaved 
    : Number((trees * 1.15 / 1000).toFixed(1));

  const budgetLakhs = Number(((data.budget || 500000) / 100000).toFixed(1));

  const stats = [
    {
      label: 'Hot Zones',
      value: data.hotZones || 446,
      suffix: '',
      icon: AlertTriangle,
      color: 'text-heat-danger',
      bg: 'bg-gradient-to-br from-heat-danger/20 to-red-900/20',
      border: 'border-heat-danger/30',
      glow: 'shadow-heat-danger/20',
      description: 'Critical areas needing immediate action'
    },
    {
      label: 'Trees Needed',
      value: trees,
      suffix: '',
      icon: Trees,
      color: 'text-heat-cool',
      bg: 'bg-gradient-to-br from-heat-cool/20 to-green-900/20',
      border: 'border-heat-cool/30',
      glow: 'shadow-heat-cool/20',
      description: 'Optimal planting for maximum cooling'
    },
    {
      label: 'Expected Cooling',
      value: Number(data.expectedCooling || 1.8),
      suffix: '°C',
      icon: TrendingDown,
      color: 'text-cyan-400',
      bg: 'bg-gradient-to-br from-cyan-500/20 to-blue-900/20',
      border: 'border-cyan-400/30',
      glow: 'shadow-cyan-400/20',
      description: 'Average temperature reduction city-wide'
    },
    {
      label: 'Budget Allocated',
      value: budgetLakhs,
      suffix: 'L',
      icon: IndianRupee,
      color: 'text-purple-400',
      bg: 'bg-gradient-to-br from-purple-500/20 to-purple-900/20',
      border: 'border-purple-400/30',
      glow: 'shadow-purple-400/20',
      description: 'Total investment for tree planting'
    },
    {
      label: 'People Benefited',
      value: Number(peopleVal),
      suffix: 'K',
      icon: Users,
      color: 'text-pink-400',
      bg: 'bg-gradient-to-br from-pink-500/20 to-pink-900/20',
      border: 'border-pink-400/30',
      glow: 'shadow-pink-400/20',
      description: 'Residents in cooling zones'
    },
    {
      label: 'Water Saved',
      value: Number(waterVal),
      suffix: 'M L/yr',
      icon: Droplets,
      color: 'text-blue-400',
      bg: 'bg-gradient-to-br from-blue-500/20 to-blue-900/20',
      border: 'border-blue-400/30',
      glow: 'shadow-blue-400/20',
      description: 'Reduced irrigation from cooling'
    },
    {
      label: 'CO₂ Absorbed',
      value: Number(co2Val),
      suffix: ' tons',
      icon: Wind,
      color: 'text-emerald-400',
      bg: 'bg-gradient-to-br from-emerald-500/20 to-emerald-900/20',
      border: 'border-emerald-400/30',
      glow: 'shadow-emerald-400/20',
      description: 'Annual carbon sequestration'
    },
    {
      label: 'Energy Saved',
      value: Number(energyVal),
      suffix: 'M kWh',
      icon: ThermometerSun,
      color: 'text-yellow-400',
      bg: 'bg-gradient-to-br from-yellow-500/20 to-yellow-900/20',
      border: 'border-yellow-400/30',
      glow: 'shadow-yellow-400/20',
      description: 'Reduced AC usage city-wide'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <TiltCard3D key={stat.label} scale={1.03}>
          <motion.div
            initial={{ opacity: 0, y: 30, rotateX: 15 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            transition={{ delay: index * 0.05, duration: 0.5, type: "spring" }}
            className={`glass-panel p-5 border ${stat.border} ${stat.glow} shadow-lg hover:shadow-xl transition-shadow duration-300 relative overflow-hidden group`}
          >
            {/* Animated gradient background */}
            <div className={`absolute inset-0 ${stat.bg} opacity-50 group-hover:opacity-70 transition-opacity`} />

            {/* Floating particles inside card */}
            <div className="absolute top-2 right-2 w-1 h-1 rounded-full bg-white/30 animate-ping" />
            <div className="absolute bottom-4 left-4 w-0.5 h-0.5 rounded-full bg-white/20 animate-pulse" />

            <div className="relative z-10">
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-400 text-xs uppercase tracking-wider font-medium">{stat.label}</span>
                <motion.div 
                  whileHover={{ rotate: 360, scale: 1.2 }}
                  transition={{ duration: 0.5 }}
                  className={`p-2.5 rounded-xl ${stat.bg} backdrop-blur-sm`}
                >
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </motion.div>
              </div>

              <div className="flex items-baseline gap-1">
                <CountUp
                  key={`${stat.label}-${stat.value}`}
                  end={stat.value}
                  duration={1.2}
                  decimals={stat.value % 1 !== 0 ? 1 : 0}
                  className={`text-3xl font-bold ${stat.color}`}
                />
                <span className={`text-lg font-semibold ${stat.color} opacity-80`}>{stat.suffix}</span>
              </div>

              <p className="text-gray-500 text-xs mt-2 leading-relaxed">{stat.description}</p>

              {/* Progress bar */}
              <div className="mt-3 h-1 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, Math.max(15, (Number(stat.value) / (Number(stat.value) * 1.3 || 1)) * 100))}%` }}
                  transition={{ delay: index * 0.05 + 0.2, duration: 1.0, ease: "easeOut" }}
                  className={`h-full rounded-full ${stat.color.replace('text-', 'bg-')}`}
                />
              </div>
            </div>
          </motion.div>
        </TiltCard3D>
      ))}
    </div>
  );
};

export default StatsCards3D;
