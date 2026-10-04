import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float } from '@react-three/drei';
import * as THREE from 'three';

function CylinderBar({ position, height, color, label, value, delay }) {
  const meshRef = useRef();
  const targetHeight = height;

  useFrame((state) => {
    if (meshRef.current) {
      // Animate height on load
      const currentScale = meshRef.current.scale.y;
      const target = targetHeight;
      meshRef.current.scale.y += (target - currentScale) * 0.05;

      // Gentle floating
      meshRef.current.position.y = (meshRef.current.scale.y / 2) + Math.sin(state.clock.elapsedTime + delay) * 0.05;
    }
  });

  return (
    <group position={position}>
      {/* Main cylinder */}
      <mesh ref={meshRef} position={[0, 0, 0]} scale={[1, 0.01, 1]}>
        <cylinderGeometry args={[0.3, 0.3, 1, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.4}
          metalness={0.6}
          roughness={0.2}
          transparent
          opacity={0.9}
        />
      </mesh>

      {/* Top cap glow */}
      <mesh position={[0, targetHeight + 0.02, 0]}>
        <cylinderGeometry args={[0.35, 0.35, 0.05, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.6} />
      </mesh>

      {/* Value label */}
      <Text
        position={[0, targetHeight + 0.5, 0]}
        fontSize={0.25}
        color="white"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000"
      >
        {value}°C
      </Text>

      {/* Ward label */}
      <Text
        position={[0, -0.3, 0]}
        fontSize={0.18}
        color="#94a3b8"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
    </group>
  );
}

function GroundPlane() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]}>
      <planeGeometry args={[12, 8]} />
      <meshStandardMaterial
        color="#0f172a"
        metalness={0.8}
        roughness={0.2}
        transparent
        opacity={0.5}
      />
    </mesh>
  );
}

function GridLines() {
  return (
    <group>
      {[...Array(11)].map((_, i) => (
        <mesh key={`v${i}`} position={[-5 + i, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.02, 6]} />
          <meshBasicMaterial color="#00f0ff" transparent opacity={0.1} />
        </mesh>
      ))}
      {[...Array(7)].map((_, i) => (
        <mesh key={`h${i}`} position={[0, 0.01, -3 + i]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[10, 0.02]} />
          <meshBasicMaterial color="#00f0ff" transparent opacity={0.1} />
        </mesh>
      ))}
    </group>
  );
}

const HeatCylinderChart = () => {
  const data = useMemo(() => [
    { label: 'W23', value: 46.8, height: 3.5, color: '#ff006e', x: -3.5 },
    { label: 'W101', value: 47.2, height: 3.8, color: '#ff006e', x: -2 },
    { label: 'W7', value: 45.2, height: 3.0, color: '#ffb703', x: -0.5 },
    { label: 'W12', value: 43.1, height: 2.4, color: '#ffb703', x: 1 },
    { label: 'W67', value: 44.3, height: 2.7, color: '#ffb703', x: 2.5 },
    { label: 'W45', value: 41.5, height: 1.8, color: '#00f0ff', x: 4 },
  ], []);

  return (
    <div className="w-full h-[400px] rounded-2xl overflow-hidden relative">
      <Canvas camera={{ position: [0, 4, 8], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[5, 8, 5]} intensity={1} color="#00f0ff" />
        <pointLight position={[-5, 5, -5]} intensity={0.5} color="#ff006e" />

        <GroundPlane />
        <GridLines />

        {data.map((d, i) => (
          <CylinderBar
            key={d.label}
            position={[d.x, 0, 0]}
            height={d.height}
            color={d.color}
            label={d.label}
            value={d.value}
            delay={i * 0.5}
          />
        ))}

        <OrbitControls
          enableZoom={true}
          enablePan={false}
          autoRotate
          autoRotateSpeed={1}
          minPolarAngle={Math.PI / 6}
          maxPolarAngle={Math.PI / 2.5}
        />
      </Canvas>

      {/* Overlay title */}
      <div className="absolute top-4 left-4 glass-panel px-4 py-2">
        <p className="text-xs text-gray-400 uppercase tracking-wider">3D Temperature Comparison</p>
        <p className="text-white font-bold text-sm">Drag to rotate • Scroll to zoom</p>
      </div>
    </div>
  );
};

export default HeatCylinderChart;
