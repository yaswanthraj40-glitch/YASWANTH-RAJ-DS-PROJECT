import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from 'recharts';
import { Zap, HelpCircle, AlertCircle } from 'lucide-react';

const API = 'http://localhost:8000';

const directionColor = (dir) => {
  if (dir === 'increases_heat') return '#ff006e';
  if (dir === 'reduces_heat') return '#00ff88';
  return '#00f0ff';
};

const SHAPExplainPanel = ({ features, zoneId, predictedLST }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const prevFeaturesRef = useRef(null);

  useEffect(() => {
    const featStr = JSON.stringify(features);
    if (featStr === prevFeaturesRef.current) return;
    prevFeaturesRef.current = featStr;

    if (!features && !zoneId) return;
    fetchExplanation();
  }, [features, zoneId]);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (zoneId) {
        const resp = await fetch(`${API}/api/model/explain/${zoneId}`);
        if (!resp.ok) throw new Error(`${resp.status}`);
        data = await resp.json();
      } else if (features) {
        const resp = await fetch(`${API}/api/predict-heat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(features),
        });
        if (!resp.ok) throw new Error(`${resp.status}`);
        const result = await resp.json();
        data = result.explanation || result;
        if (result.predicted_lst_c) {
          data.predicted_lst_c = result.predicted_lst_c;
        }
      }
      setExplanation(data);
    } catch (err) {
      setError(`Explanation unavailable: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const contributions = explanation?.top_heat_drivers || explanation?.explanation?.top_heat_drivers || [];
  const allContributions = [
    ...(explanation?.top_heat_drivers || []),
    ...(explanation?.cooling_factors || []),
  ].sort((a, b) => b.percentage - a.percentage);

  const lst = explanation?.predicted_lst_c || predictedLST;
  const risk = explanation?.heat_risk || explanation?.explanation?.heat_risk;
  const riskColor = explanation?.heat_risk_color || explanation?.explanation?.heat_risk_color || '#ffb703';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-500 gap-2">
        <Zap className="w-4 h-4 animate-pulse text-cyan-400" />
        Computing SHAP explanations...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        {error}
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-gray-600 gap-2">
        <HelpCircle className="w-8 h-8" />
        <p className="text-sm">Select a heat zone on the map to see SHAP explanation</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header + Risk */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-white">Why is this area hot?</h4>
          <p className="text-gray-400 text-xs mt-0.5">
            {explanation?.method || 'Feature attribution from trained model'}
          </p>
        </div>
        {risk && (
          <div
            className="px-3 py-1 rounded-full text-xs font-bold border"
            style={{ borderColor: `${riskColor}50`, backgroundColor: `${riskColor}20`, color: riskColor }}
          >
            {risk} HEAT RISK
          </div>
        )}
      </div>

      {/* Predicted LST */}
      {lst && (
        <div className="p-3 rounded-xl bg-white/5 flex justify-between items-center">
          <span className="text-gray-400 text-sm">Predicted LST</span>
          <span className="text-2xl font-black" style={{ color: riskColor }}>
            {lst.toFixed(1)}°C
          </span>
        </div>
      )}

      {/* SHAP Bar Chart */}
      {allContributions.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Feature Contributions (%)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={allContributions.slice(0, 8)}
              layout="vertical"
              margin={{ top: 0, right: 40, left: 120, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
              <XAxis
                type="number"
                stroke="#4b5563"
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                tickFormatter={v => `${v.toFixed(0)}%`}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={115}
                stroke="#4b5563"
                tick={{ fill: '#9ca3af', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  border: '1px solid rgba(0, 240, 255, 0.3)',
                  borderRadius: '10px',
                  color: '#fff',
                  fontSize: '11px',
                }}
                formatter={(val, name, props) => [
                  `${val?.toFixed(1)}% ${props.payload.contribution_direction === 'increases_heat' ? '🔥' : '🌿'}`,
                  'Contribution'
                ]}
              />
              <Bar dataKey="percentage" radius={[0, 4, 4, 0]}>
                {allContributions.slice(0, 8).map((c, i) => (
                  <Cell key={i} fill={directionColor(c.contribution_direction)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Human explanation */}
      {explanation?.human_explanation && (
        <div className="p-3 rounded-xl bg-slate-800/60 border border-white/10">
          <p className="text-gray-300 text-xs leading-relaxed">
            💡 {explanation.human_explanation}
          </p>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 text-[10px] text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#ff006e]" />
          <span>Increases heat</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-[#00ff88]" />
          <span>Reduces heat</span>
        </div>
      </div>

      <p className="text-gray-600 text-[10px]">
        {explanation?.method?.includes('SHAP')
          ? 'Values from SHAP TreeExplainer — actual model attribution.'
          : 'Values from XGBoost feature importance — install shap for SHAP-based attribution.'}
      </p>
    </div>
  );
};

export default SHAPExplainPanel;
