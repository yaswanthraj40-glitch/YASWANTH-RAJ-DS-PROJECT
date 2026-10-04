import React from 'react';
import Tilt from 'react-parallax-tilt';
import { motion } from 'framer-motion';

const TiltCard3D = ({ children, className = '', glareEnable = true, scale = 1.05 }) => {
  return (
    <Tilt
      tiltMaxAngleX={15}
      tiltMaxAngleY={15}
      perspective={1000}
      scale={scale}
      transitionSpeed={1500}
      gyroscope={true}
      glareEnable={glareEnable}
      glareMaxOpacity={0.15}
      glareColor="#00f0ff"
      glarePosition="all"
      className={className}
    >
      <motion.div
        initial={{ opacity: 0, rotateY: -30 }}
        animate={{ opacity: 1, rotateY: 0 }}
        transition={{ duration: 0.8, type: "spring" }}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {children}
      </motion.div>
    </Tilt>
  );
};

export default TiltCard3D;
