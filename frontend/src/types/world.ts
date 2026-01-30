/** Type definitions matching the backend schemas. */

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export interface Color {
  r: number;
  g: number;
  b: number;
}

export interface GeometryParams {
  type: 'box' | 'sphere' | 'cylinder' | 'cone' | 'torus' | 'plane' | 'custom';
  width?: number;
  height?: number;
  depth?: number;
  radius?: number;
  radius_top?: number;
  radius_bottom?: number;
  tube?: number;
  width_segments?: number;
  height_segments?: number;
  radial_segments?: number;
  tubular_segments?: number;
  vertices?: number[];
  indices?: number[];
  normals?: number[];
  uvs?: number[];
}

export interface MaterialParams {
  color: Color;
  emissive?: Color;
  emissive_intensity: number;
  metalness: number;
  roughness: number;
  opacity: number;
  transparent: boolean;
  wireframe: boolean;
  flat_shading: boolean;
}

export interface PhysicsParams {
  has_gravity: boolean;
  is_static: boolean;
  mass: number;
  friction: number;
  restitution: number;
}

export interface AnimationParams {
  type: 'none' | 'rotate' | 'bob' | 'orbit';
  speed: number;
  axis: Vec3;
  amplitude: number;
}

export interface WorldObject {
  id: string;
  name: string;
  description: string;
  position: Vec3;
  rotation: Vec3;
  scale: Vec3;
  geometry: GeometryParams;
  material: MaterialParams;
  physics: PhysicsParams;
  animation: AnimationParams;
  children: WorldObject[];
  tags: string[];
  metadata: Record<string, unknown>;
}

export interface EnvironmentSettings {
  sky_color: Color;
  ground_color: Color;
  fog_color: Color | null;
  fog_near: number;
  fog_far: number;
  fog_enabled: boolean;
  ambient_light_color: Color;
  ambient_light_intensity: number;
  sun_color: Color;
  sun_intensity: number;
  sun_position: Vec3;
  time_of_day: string;
}

export interface TerrainParams {
  type: 'flat' | 'hills' | 'mountains' | 'water';
  size: number;
  height: number;
  color: Color;
  segments: number;
  seed: number | null;
}

export type MessageType =
  | 'user_input'
  | 'object_created'
  | 'object_modified'
  | 'object_removed'
  | 'environment_updated'
  | 'terrain_created'
  | 'narration'
  | 'status'
  | 'error'
  | 'world_state';

export interface WSMessage {
  type: MessageType;
  data: Record<string, unknown>;
}
