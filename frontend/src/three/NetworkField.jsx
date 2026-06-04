import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const PALETTE = [
  new THREE.Color("#7c5cff"),
  new THREE.Color("#22d3ee"),
  new THREE.Color("#00f5a0"),
  new THREE.Color("#9b82ff"),
];

function Constellation({ count = 130, radius = 4.2 }) {
  const group = useRef();

  const { positions, colors, linePositions } = useMemo(() => {
    const pts = [];
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      // Random point inside a sphere (rejection-free via cube-root radius).
      const r = radius * Math.cbrt(Math.random());
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);
      pts.push(new THREE.Vector3(x, y, z));
      positions.set([x, y, z], i * 3);
      const c = PALETTE[(Math.random() * PALETTE.length) | 0];
      colors.set([c.r, c.g, c.b], i * 3);
    }

    // Connect nodes that are close together → service-mesh look.
    const lines = [];
    const maxDist = 1.35;
    for (let i = 0; i < count; i++) {
      let links = 0;
      for (let j = i + 1; j < count && links < 3; j++) {
        if (pts[i].distanceTo(pts[j]) < maxDist) {
          lines.push(pts[i].x, pts[i].y, pts[i].z, pts[j].x, pts[j].y, pts[j].z);
          links++;
        }
      }
    }
    return { positions, colors, linePositions: new Float32Array(lines) };
  }, [count, radius]);

  useFrame((state, delta) => {
    if (!group.current) return;
    group.current.rotation.y += delta * 0.05;
    group.current.rotation.x += delta * 0.012;
    // Subtle parallax toward the pointer.
    const px = state.pointer.x * 0.6;
    const py = state.pointer.y * 0.4;
    group.current.position.x += (px - group.current.position.x) * 0.04;
    group.current.position.y += (py - group.current.position.y) * 0.04;
  });

  return (
    <group ref={group}>
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={linePositions.length / 3}
            array={linePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          color="#3a3f63"
          transparent
          opacity={0.32}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>

      <points>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={positions.length / 3}
            array={positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={colors.length / 3}
            array={colors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.075}
          vertexColors
          transparent
          opacity={0.95}
          sizeAttenuation
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

/**
 * Full-bleed animated 3D node network. Sits behind the hero content.
 */
export default function NetworkField({ className = "" }) {
  return (
    <div className={className} aria-hidden="true">
      <Canvas
        camera={{ position: [0, 0, 9], fov: 60 }}
        dpr={[1, 1.8]}
        gl={{ antialias: true, alpha: true }}
      >
        <Constellation />
      </Canvas>
    </div>
  );
}
