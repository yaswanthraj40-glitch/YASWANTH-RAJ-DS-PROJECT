import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Brain, TrendingUp, AlertCircle, CheckCircle, Info } from 'lucide-react';

const API = 'http://localhost:8000';

const MetricCard = ({ label, value, unit, description, color = 'cyan' }) => {
  const colorMap = {
    cyan: { bg: 'from-cyan-500/10 to-cyan-900/10', border: 'border-cyan-500/20', text: 'text-cyan-400' },
    green: { bg: 'from-emerald-500/10 to-emerald-900/10', border: 'border-emerald-500/20', text: 'text-emerald-400' },
    purple: { bg: 'from-purple-500/10 to-purple-900/10', border: 'border-purple-500/20', text: 'text-purple-400' },
    orange: { bg: 'from-orange-500/10 to-orange-900/10', border: 'border-orange-500/20', text: 'text-orange-400' },
  };
  const c = colorMap[color] || colorMap.cyan;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-xl bg-gradient-to-br ${c.bg} border ${c.border}`}
    >
      <p className="text-gray-400 text-xs mb-1">{label}</p>
      <p className={`text-2xl font-black ${c.text}`}>
        {value !== null && value !== undefined ? value : '–'}
        {unit && <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>}
      </p>
      {description && <p className="text-gray-500 text-[10px] mt-1">{description}</p>}
    </motion.div>
  );
};

const ModelPerformancePanel = () => {
  const [metrics, setMetrics] = useState(null);
  const [importance, setImportance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/model/metrics`).then(r => r.json()),
      fetch(`${API}/api/model/importance`).then(r => r.json()),
    ])
      .then(([m, imp]) => {
        setMetrics(m);
        setImportance(imp);
      })
      .catch(err => setError('Backend offline — run uvicorn main:app --reload'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-gray-500">
        <Brain className="w-6 h-6 animate-pulse mr-2" /> Loading model metrics...
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        {error || 'Model metrics unavailable'}
      </div>
    );
  }

  const m = metrics.metrics || {};
  const dataset = metrics.dataset || {};
  const fi = importance?.feature_importances || [];
  const modelLoaded = metrics.model_loaded;

  // Chart colors
  const barColors = ['#00f0ff', '#a855f7', '#ff006e', '#ffb703', '#00ff88', '#60a5fa', '#f472b6', '#fbbf24', '#34d399'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold gradient-text">Model Performance</h3>
          <p className="text-gray-400 text-xs mt-0.5">
            {metrics.model_type || 'XGBoost Regressor'} •{' '}
            {metrics.training_date ? new Date(metrics.training_date).toLocaleDateString() : 'Unknown date'}
          </p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold ${
          modelLoaded
            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
            : 'bg-red-500/10 border border-red-500/20 text-red-400'
        }`}>
          {modelLoaded ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
          {modelLoaded ? 'Model Loaded' : 'Model Not Loaded'}
        </div>
      </div>

      {/* Training data note */}
      {metrics.training_data_note && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
          <Info className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
          <p className="text-yellow-300 text-xs leading-relaxed">{metrics.training_data_note}</p>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="Mean Absolute Error (MAE)"
          value={m.mae_celsius !== null ? m.mae_celsius?.toFixed(3) : null}
          unit="°C"
          description="Average prediction error on test set"
          color="cyan"
        />
        <MetricCard
          label="Root Mean Squared Error"
          value={m.rmse_celsius !== null ? m.rmse_celsius?.toFixed(3) : null}
          unit="°C"
          description="Penalizes large errors more than MAE"
          color="purple"
        />
        <MetricCard
          label="R² Score"
          value={m.r2_score !== null ? (m.r2_score * 100)?.toFixed(1) : null}
          unit="%"
          description="Variance in LST explained by the model"
          color="green"
        />
        <MetricCard
          label="Cross-Val MAE (5-Fold)"
          value={m.cv_mae_mean !== null ? `${m.cv_mae_mean?.toFixed(3)} ±${m.cv_mae_std?.toFixed(3)}` : null}
          unit="°C"
          description="Generalization across 5 folds"
          color="orange"
        />
      </div>

      {/* Dataset info */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: 'Total Samples', value: dataset.total_samples },
          { label: 'Train Samples', value: dataset.train_samples },
          { label: 'Test Samples', value: dataset.test_samples },
        ].map(item => (
          <div key={item.label} className="p-3 rounded-xl bg-white/5">
            <p className="text-white font-bold text-lg">{item.value ?? '–'}</p>
            <p className="text-gray-400 text-xs">{item.label}</p>
          </div>
        ))}
      </div>

      {/* Feature Importance Chart */}
      {fi.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h4 className="text-sm font-semibold text-white">Feature Importance</h4>
            <span className="text-gray-500 text-xs">({importance?.method || 'gain-based'})</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              data={fi.slice(0, 9)}
              layout="vertical"
              margin={{ top: 0, right: 30, left: 120, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={v => `${v.toFixed(0)}%`}
                stroke="#4b5563"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
              />
              <YAxis
                type="category"
                dataKey="label"
                stroke="#4b5563"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                width={115}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(0, 240, 255, 0.3)',
                  borderRadius: '10px',
                  color: '#fff',
                  fontSize: '12px',
                }}
                formatter={(value) => [`${value?.toFixed(1)}%`, 'Importance']}
              />
              <Bar dataKey="percentage" radius={[0, 4, 4, 0]}>
                {fi.slice(0, 9).map((_, index) => (
                  <Cell key={index} fill={barColors[index % barColors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="text-gray-600 text-[10px] text-center">
        All metrics computed from actual model training — not hardcoded values.
      </p>
    </div>
  );
};

export default ModelPerformancePanel;
