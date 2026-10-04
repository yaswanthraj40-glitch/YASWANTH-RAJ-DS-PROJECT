import React from 'react';
import { motion } from 'framer-motion';
import { ThermometerSun, Trees, TrendingDown, AlertTriangle, IndianRupee, Users } from 'lucide-react';

const StatsCards = ({ data }) => {
  const stats = [
    {
      label: 'Hot Zones',
      value: data.hotZones,
      icon: AlertTriangle,
      color: 'text-heat-danger',
      bg: 'bg-heat-danger/10',
      border: 'border-heat-danger/20'
    },
    {
      label: 'Trees Needed',
      value: data.recommendedTrees.toLocaleString(),
      icon: Trees,
      color: 'text-heat-cool',
      bg: 'bg-heat-cool/10',
      border: 'border-heat-cool/20'
    },
    {
      label: 'Expected Cooling',
      value: `-${data.expectedCooling}°C`,
      icon: TrendingDown,
      color: 'text-cyan-400',
      bg: 'bg-cyan-400/10',
      border: 'border-cyan-400/20'
    },
    {
      label: 'Budget Allocated',
      value: `₹${(data.budget / 100000).toFixed(1)}L`,
      icon: IndianRupee,
      color: 'text-purple-400',
      bg: 'bg-purple-400/10',
      border: 'border-purple-400/20'
    }
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          whileHover={{ scale: 1.02, y: -2 }}
          className={`glass-panel p-4 border ${stat.border} cursor-pointer`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">{stat.label}</span>
            <div className={`p-2 rounded-lg ${stat.bg}`}>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
          </div>
          <motion.p 
            className={`text-2xl font-bold ${stat.color}`}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
          >
            {stat.value}
          </motion.p>
        </motion.div>
      ))}
    </div>
  );
};

export default StatsCards;
