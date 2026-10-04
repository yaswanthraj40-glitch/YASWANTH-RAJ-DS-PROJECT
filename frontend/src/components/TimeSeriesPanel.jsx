import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Clock, Sun, Sunset, Moon, AlertTriangle, Info } from 'lucide-react';

const API = 'http://localhost:8000';

const periodIcons = { morning: Sun, noon: Sun, afternoon: Sunset, evening: Moon };
const periodColors = { morning: '#ffb703', noon: '#ff006e', afternoon: '#ff4444', evening: '#a855f7' };

const TimeSeriesPanel = ({ lat = 13.0827, lng = 80.2707 }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTimeseries(selectedDate);
  }, [selectedDate, lat, lng]);

  const fetchTimeseries = async (date) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `${API}/api/heat/timeseries?date=${date}&lat=${lat}&lng=${lng}`
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const result = await resp.json();
      setData(result);
    } catch (err) {
      setError(`Timeseries unavailable: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const peak = data?.peak_hour;

  const periodStats = [
    { label: 'Morning', key: 'morning_avg', time: '06–10', icon: Sun, color: '#ffb703' },
    { label: 'Noon', key: 'noon_avg', time: '10–14', icon: Sun, color: '#ff006e' },
    { label: 'Afternoon', key: 'afternoon_avg', time: '14–18', icon: Sunset, color: '#ff4444' },
    { label: 'Evening', key: 'evening_avg', time: '18–22', icon: Moon, color: '#a855f7' },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-lg font-bold gradient-text">Temporal Heat Analysis</h3>
          <p className="text-gray-400 text-xs mt-0.5">Hourly temperature pattern — air temp (real) + LST estimate</p>
        </div>
        <input
          type="date"
          value={selectedDate}
          max={new Date().toISOString().split('T')[0]}
          onChange={e => setSelectedDate(e.target.value)}
          className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
        />
      </div>

      {/* Demo / Source label */}
      {data && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs border ${
          data.is_demo
            ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
            : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
        }`}>
          {data.is_demo ? <AlertTriangle className="w-3.5 h-3.5" /> : <Info className="w-3.5 h-3.5" />}
          <span className="font-medium">{data.is_demo ? 'DEMO DATA' : 'REAL DATA'}</span>
          <span className="text-gray-500">— {data.source}</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40 text-gray-500 gap-2">
          <Clock className="w-4 h-4 animate-spin text-cyan-400" />
          Loading time-series...
        </div>
      ) : error ? (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
          {error}
        </div>
      ) : data ? (
        <>
          {/* Chart */}
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data.timeseries} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="lstGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff006e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff006e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="airGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#00f0ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="time"
                stroke="#4b5563"
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                interval={3}
              />
              <YAxis
                stroke="#4b5563"
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                tickFormatter={v => `${v}°`}
                domain={['dataMin - 2', 'dataMax + 2']}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(0, 240, 255, 0.3)',
                  borderRadius: '10px',
                  color: '#fff',
                  fontSize: '11px',
                }}
                formatter={(value, name) => [
                  `${value?.toFixed(1)}°C`,
                  name === 'estimated_lst_c' ? 'Est. Surface Temp (ESTIMATED)' : 'Air Temperature (Real)'
                ]}
              />
              {/* Peak hour reference */}
              {peak && (
                <ReferenceLine
                  x={peak.time}
                  stroke="#ff006e"
                  strokeDasharray="4 2"
                  label={{ value: 'PEAK', position: 'top', fill: '#ff006e', fontSize: 10 }}
                />
              )}
              <Area
                type="monotone"
                dataKey="air_temp_c"
                stroke="#00f0ff"
                strokeWidth={1.5}
                fill="url(#airGrad)"
                name="air_temp_c"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="estimated_lst_c"
                stroke="#ff006e"
                strokeWidth={2}
                fill="url(#lstGrad)"
                name="estimated_lst_c"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="flex items-center gap-4 text-[10px] text-gray-500 justify-center">
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-0.5 bg-[#00f0ff]" />
              <span>Air Temp (Real, Open-Meteo)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-0.5 bg-[#ff006e]" />
              <span>Est. Surface Temp (ESTIMATED)</span>
            </div>
          </div>

          {/* Period Stats */}
          <div className="grid grid-cols-4 gap-2">
            {periodStats.map(period => {
              const val = data[period.key];
              const Icon = period.icon;
              return (
                <motion.div
                  key={period.key}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 rounded-xl bg-white/5 border border-white/5 text-center"
                  style={{ borderColor: `${period.color}20` }}
                >
                  <Icon className="w-4 h-4 mx-auto mb-1" style={{ color: period.color }} />
                  <p className="text-[10px] text-gray-400">{period.label}</p>
                  <p className="text-sm font-bold" style={{ color: period.color }}>
                    {val ? `${val}°C` : '–'}
                  </p>
                  <p className="text-[9px] text-gray-600">{period.time}:00</p>
                </motion.div>
              );
            })}
          </div>

          {/* Peak */}
          {peak && (
            <div className="flex items-center justify-between p-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <span className="text-gray-400 text-xs">Peak Heat Time</span>
              <div className="text-right">
                <p className="text-red-400 font-bold">{peak.time}</p>
                <p className="text-xs text-gray-400">{peak.estimated_lst_c}°C (ESTIMATED)</p>
              </div>
            </div>
          )}

          {/* Note */}
          <p className="text-gray-600 text-[10px]">
            {data.lst_note}
          </p>
        </>
      ) : null}
    </div>
  );
};

export default TimeSeriesPanel;
