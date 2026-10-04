import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Thermometer, Trees, Users, IndianRupee, MapPin } from 'lucide-react';
import TiltCard3D from './TiltCard3D';

const wards = [
  {
    id: 23,
    name: 'Ward 23',
    temp: 46.8,
    population: 35000,
    income: 2,
    trees: 150,
    cost: 75000,
    cooling: 3.5,
    priority: 'CRITICAL',
    color: '#ff006e',
    coordinates: '13.085°N, 80.275°E',
    buildings: 85,
    greenCover: 3
  },
  {
    id: 101,
    name: 'Ward 101',
    temp: 47.2,
    population: 42000,
    income: 2,
    trees: 180,
    cost: 90000,
    cooling: 4.1,
    priority: 'CRITICAL',
    color: '#ff006e',
    coordinates: '13.092°N, 80.281°E',
    buildings: 90,
    greenCover: 2
  },
  {
    id: 7,
    name: 'Ward 7',
    temp: 45.2,
    population: 28000,
    income: 3,
    trees: 120,
    cost: 60000,
    cooling: 2.8,
    priority: 'HIGH',
    color: '#ffb703',
    coordinates: '13.078°N, 80.268°E',
    buildings: 78,
    greenCover: 5
  },
  {
    id: 45,
    name: 'Ward 45',
    temp: 41.5,
    population: 22000,
    income: 7,
    trees: 80,
    cost: 40000,
    cooling: 1.8,
    priority: 'MEDIUM',
    color: '#00f0ff',
    coordinates: '13.065°N, 80.255°E',
    buildings: 65,
    greenCover: 12
  },
  {
    id: 67,
    name: 'Ward 67',
    temp: 44.3,
    population: 31000,
    income: 4,
    trees: 110,
    cost: 55000,
    cooling: 2.5,
    priority: 'HIGH',
    color: '#ffb703',
    coordinates: '13.088°N, 80.290°E',
    buildings: 82,
    greenCover: 4
  }
];

const WardCarousel3D = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);

  const slideVariants = {
    enter: (direction) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
      rotateY: direction > 0 ? 45 : -45,
      scale: 0.8
    }),
    center: {
      x: 0,
      opacity: 1,
      rotateY: 0,
      scale: 1
    },
    exit: (direction) => ({
      x: direction < 0 ? 300 : -300,
      opacity: 0,
      rotateY: direction < 0 ? 45 : -45,
      scale: 0.8
    })
  };

  const paginate = (newDirection) => {
    setDirection(newDirection);
    setCurrentIndex((prev) => {
      let next = prev + newDirection;
      if (next < 0) next = wards.length - 1;
      if (next >= wards.length) next = 0;
      return next;
    });
  };

  const ward = wards[currentIndex];

  return (
    <div className="glass-panel p-6 relative" style={{ perspective: '1000px' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold gradient-text">Priority Ward Analysis</h3>
          <p className="text-gray-400 text-sm mt-1">3D card view of high-priority cooling zones</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => paginate(-1)}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-400 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => paginate(1)}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-400 transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="relative h-[320px] flex items-center justify-center" style={{ perspective: '1000px' }}>
        <AnimatePresence initial={false} custom={direction}>
          <motion.div
            key={currentIndex}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="absolute w-full max-w-lg"
            style={{ transformStyle: 'preserve-3d' }}
          >
            <TiltCard3D scale={1.02}>
              <div className="glass-panel p-6 border-2 relative overflow-hidden" style={{ borderColor: `${ward.color}40` }}>
                {/* Priority badge */}
                <div 
                  className="absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-bold"
                  style={{ backgroundColor: `${ward.color}20`, color: ward.color, border: `1px solid ${ward.color}40` }}
                >
                  {ward.priority}
                </div>

                {/* 3D Ring decoration */}
                <div 
                  className="absolute -right-10 -top-10 w-40 h-40 rounded-full opacity-10"
                  style={{ border: `3px solid ${ward.color}` }}
                />

                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-4">
                    <div 
                      className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold"
                      style={{ backgroundColor: `${ward.color}20`, color: ward.color }}
                    >
                      {ward.id}
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-white">{ward.name}</h4>
                      <div className="flex items-center gap-1 text-gray-400 text-xs">
                        <MapPin className="w-3 h-3" />
                        {ward.coordinates}
                      </div>
                    </div>
                  </div>

                  {/* Temperature Gauge */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">Surface Temperature</span>
                      <span className="font-bold" style={{ color: ward.color }}>{ward.temp}°C</span>
                    </div>
                    <div className="h-3 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${((ward.temp - 35) / 15) * 100}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: ward.color }}
                      />
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl bg-white/5 flex items-center gap-3">
                      <Users className="w-4 h-4 text-cyan-400" />
                      <div>
                        <p className="text-xs text-gray-400">Population</p>
                        <p className="text-white font-bold">{ward.population.toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 flex items-center gap-3">
                      <Trees className="w-4 h-4 text-heat-cool" />
                      <div>
                        <p className="text-xs text-gray-400">Trees</p>
                        <p className="text-white font-bold">{ward.trees}</p>
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 flex items-center gap-3">
                      <IndianRupee className="w-4 h-4 text-purple-400" />
                      <div>
                        <p className="text-xs text-gray-400">Cost</p>
                        <p className="text-white font-bold">₹{ward.cost.toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-white/5 flex items-center gap-3">
                      <Thermometer className="w-4 h-4 text-heat-cool" />
                      <div>
                        <p className="text-xs text-gray-400">Cooling</p>
                        <p className="text-white font-bold">-{ward.cooling}°C</p>
                      </div>
                    </div>
                  </div>

                  {/* Income indicator */}
                  <div className="mt-4 flex items-center gap-2">
                    <span className="text-xs text-gray-400">Income Level:</span>
                    <div className="flex gap-1">
                      {[...Array(10)].map((_, i) => (
                        <div
                          key={i}
                          className="w-3 h-3 rounded-sm"
                          style={{ 
                            backgroundColor: i < ward.income ? ward.color : 'rgba(255,255,255,0.1)',
                            opacity: i < ward.income ? 1 : 0.3
                          }}
                        />
                      ))}
                    </div>
                    <span className="text-xs" style={{ color: ward.color }}>{ward.income}/10</span>
                  </div>
                </div>
              </div>
            </TiltCard3D>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Dots indicator */}
      <div className="flex justify-center gap-2 mt-4">
        {wards.map((_, i) => (
          <button
            key={i}
            onClick={() => {
              setDirection(i > currentIndex ? 1 : -1);
              setCurrentIndex(i);
            }}
            className={`w-2 h-2 rounded-full transition-all ${
              i === currentIndex ? 'w-6 bg-cyan-400' : 'bg-white/20 hover:bg-white/40'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default WardCarousel3D;
