/**
 * Three.js scene manager - handles the 3D environment,
 * camera, controls, lighting, and object rendering.
 */

import * as THREE from 'three';
import type {
  WorldObject,
  EnvironmentSettings,
  TerrainParams,
  AnimationParams,
  Vec3,
} from '../types/world';

interface AnimatedObject {
  mesh: THREE.Object3D;
  animation: AnimationParams;
  startTime: number;
  basePosition: Vec3;
}

export class SceneManager {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private ambientLight: THREE.AmbientLight;
  private sunLight: THREE.DirectionalLight;
  private objects: Map<string, THREE.Object3D> = new Map();
  private animatedObjects: AnimatedObject[] = [];
  private clock: THREE.Clock;
  private moveState = { forward: false, backward: false, left: false, right: false };
  private mouseState = { isLocked: false, yaw: 0, pitch: 0 };
  private readonly moveSpeed = 8;

  constructor(container: HTMLElement) {
    this.clock = new THREE.Clock();

    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0.53, 0.81, 0.92);

    // Camera - first person
    this.camera = new THREE.PerspectiveCamera(
      75,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, 1.6, 5);

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    container.appendChild(this.renderer.domElement);

    // Lights
    this.ambientLight = new THREE.AmbientLight(0x666666, 0.6);
    this.scene.add(this.ambientLight);

    this.sunLight = new THREE.DirectionalLight(0xfff3cc, 1.0);
    this.sunLight.position.set(50, 100, 50);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.width = 2048;
    this.sunLight.shadow.mapSize.height = 2048;
    this.sunLight.shadow.camera.near = 0.5;
    this.sunLight.shadow.camera.far = 500;
    this.sunLight.shadow.camera.left = -100;
    this.sunLight.shadow.camera.right = 100;
    this.sunLight.shadow.camera.top = 100;
    this.sunLight.shadow.camera.bottom = -100;
    this.scene.add(this.sunLight);

    // Hemisphere light for more natural outdoor lighting
    const hemiLight = new THREE.HemisphereLight(0x87ceeb, 0x556b2f, 0.3);
    this.scene.add(hemiLight);

    // Default ground plane
    const groundGeo = new THREE.PlaneGeometry(200, 200);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x567d46,
      roughness: 0.9,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);
    this.objects.set('__ground', ground);

    // Input handling
    this.setupControls(container);

    // Resize
    window.addEventListener('resize', () => {
      this.camera.aspect = container.clientWidth / container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(container.clientWidth, container.clientHeight);
    });

    // Start render loop
    this.animate();
  }

  private setupControls(container: HTMLElement): void {
    // Pointer lock for mouse look
    container.addEventListener('click', () => {
      container.requestPointerLock();
    });

    document.addEventListener('pointerlockchange', () => {
      this.mouseState.isLocked = document.pointerLockElement === container;
    });

    document.addEventListener('mousemove', (e) => {
      if (!this.mouseState.isLocked) return;
      this.mouseState.yaw -= e.movementX * 0.002;
      this.mouseState.pitch -= e.movementY * 0.002;
      this.mouseState.pitch = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.mouseState.pitch));
    });

    // WASD movement
    document.addEventListener('keydown', (e) => {
      switch (e.code) {
        case 'KeyW': this.moveState.forward = true; break;
        case 'KeyS': this.moveState.backward = true; break;
        case 'KeyA': this.moveState.left = true; break;
        case 'KeyD': this.moveState.right = true; break;
      }
    });

    document.addEventListener('keyup', (e) => {
      switch (e.code) {
        case 'KeyW': this.moveState.forward = false; break;
        case 'KeyS': this.moveState.backward = false; break;
        case 'KeyA': this.moveState.left = false; break;
        case 'KeyD': this.moveState.right = false; break;
      }
    });
  }

  private animate(): void {
    requestAnimationFrame(() => this.animate());

    const delta = this.clock.getDelta();
    const elapsed = this.clock.getElapsedTime();

    // Camera rotation
    const euler = new THREE.Euler(this.mouseState.pitch, this.mouseState.yaw, 0, 'YXZ');
    this.camera.quaternion.setFromEuler(euler);

    // Movement
    const direction = new THREE.Vector3();
    if (this.moveState.forward) direction.z -= 1;
    if (this.moveState.backward) direction.z += 1;
    if (this.moveState.left) direction.x -= 1;
    if (this.moveState.right) direction.x += 1;

    if (direction.lengthSq() > 0) {
      direction.normalize();
      direction.applyQuaternion(this.camera.quaternion);
      direction.y = 0; // Keep on ground
      direction.normalize();
      this.camera.position.addScaledVector(direction, this.moveSpeed * delta);
    }

    // Animate objects
    for (const animated of this.animatedObjects) {
      const t = (elapsed - animated.startTime) * animated.animation.speed;
      const mesh = animated.mesh;

      switch (animated.animation.type) {
        case 'rotate':
          mesh.rotation.x = animated.animation.axis.x * t;
          mesh.rotation.y = animated.animation.axis.y * t;
          mesh.rotation.z = animated.animation.axis.z * t;
          break;
        case 'bob':
          mesh.position.y =
            animated.basePosition.y +
            Math.sin(t) * animated.animation.amplitude;
          break;
        case 'orbit': {
          const r = animated.animation.amplitude || 5;
          mesh.position.x = animated.basePosition.x + Math.cos(t) * r;
          mesh.position.z = animated.basePosition.z + Math.sin(t) * r;
          break;
        }
      }
    }

    this.renderer.render(this.scene, this.camera);
  }

  addObject(data: WorldObject): void {
    const group = this.createMeshFromData(data);
    group.position.set(data.position.x, data.position.y, data.position.z);
    group.rotation.set(data.rotation.x, data.rotation.y, data.rotation.z);
    group.scale.set(data.scale.x, data.scale.y, data.scale.z);
    group.castShadow = true;
    group.receiveShadow = true;

    this.scene.add(group);
    this.objects.set(data.name, group);

    if (data.animation.type !== 'none') {
      this.animatedObjects.push({
        mesh: group,
        animation: data.animation,
        startTime: this.clock.getElapsedTime(),
        basePosition: { ...data.position },
      });
    }

    // Add children
    for (const child of data.children) {
      const childMesh = this.createMeshFromData(child);
      childMesh.position.set(child.position.x, child.position.y, child.position.z);
      childMesh.rotation.set(child.rotation.x, child.rotation.y, child.rotation.z);
      childMesh.scale.set(child.scale.x, child.scale.y, child.scale.z);
      childMesh.castShadow = true;
      childMesh.receiveShadow = true;
      group.add(childMesh);

      if (child.animation.type !== 'none') {
        this.animatedObjects.push({
          mesh: childMesh,
          animation: child.animation,
          startTime: this.clock.getElapsedTime(),
          basePosition: { ...child.position },
        });
      }
    }
  }

  private createMeshFromData(data: WorldObject): THREE.Mesh {
    const geometry = this.createGeometry(data.geometry);
    const material = this.createMaterial(data.material);
    return new THREE.Mesh(geometry, material);
  }

  private createGeometry(params: WorldObject['geometry']): THREE.BufferGeometry {
    switch (params.type) {
      case 'box':
        return new THREE.BoxGeometry(
          params.width ?? 1,
          params.height ?? 1,
          params.depth ?? 1
        );
      case 'sphere':
        return new THREE.SphereGeometry(
          params.radius ?? 0.5,
          params.width_segments ?? 32,
          params.height_segments ?? 16
        );
      case 'cylinder':
        return new THREE.CylinderGeometry(
          params.radius_top ?? 0.5,
          params.radius_bottom ?? 0.5,
          params.height ?? 1,
          params.radial_segments ?? 32
        );
      case 'cone':
        return new THREE.ConeGeometry(
          params.radius ?? 0.5,
          params.height ?? 1,
          params.radial_segments ?? 32
        );
      case 'torus':
        return new THREE.TorusGeometry(
          params.radius ?? 1,
          params.tube ?? 0.4,
          params.radial_segments ?? 16,
          params.tubular_segments ?? 48
        );
      case 'plane':
        return new THREE.PlaneGeometry(
          params.width ?? 1,
          params.height ?? 1,
          params.width_segments ?? 1,
          params.height_segments ?? 1
        );
      case 'custom': {
        const geo = new THREE.BufferGeometry();
        if (params.vertices) {
          geo.setAttribute(
            'position',
            new THREE.Float32BufferAttribute(params.vertices, 3)
          );
        }
        if (params.indices) {
          geo.setIndex(params.indices);
        }
        if (params.normals) {
          geo.setAttribute(
            'normal',
            new THREE.Float32BufferAttribute(params.normals, 3)
          );
        } else {
          geo.computeVertexNormals();
        }
        if (params.uvs) {
          geo.setAttribute(
            'uv',
            new THREE.Float32BufferAttribute(params.uvs, 2)
          );
        }
        return geo;
      }
      default:
        return new THREE.BoxGeometry(1, 1, 1);
    }
  }

  private createMaterial(params: WorldObject['material']): THREE.MeshStandardMaterial {
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(params.color.r, params.color.g, params.color.b),
      metalness: params.metalness,
      roughness: params.roughness,
      opacity: params.opacity,
      transparent: params.transparent,
      wireframe: params.wireframe,
      flatShading: params.flat_shading,
    });

    if (params.emissive) {
      mat.emissive = new THREE.Color(params.emissive.r, params.emissive.g, params.emissive.b);
      mat.emissiveIntensity = params.emissive_intensity;
    }

    return mat;
  }

  modifyObject(data: WorldObject): void {
    const existing = this.objects.get(data.name);
    if (!existing) return;

    existing.position.set(data.position.x, data.position.y, data.position.z);
    existing.rotation.set(data.rotation.x, data.rotation.y, data.rotation.z);
    existing.scale.set(data.scale.x, data.scale.y, data.scale.z);

    if (existing instanceof THREE.Mesh) {
      const newMat = this.createMaterial(data.material);
      existing.material = newMat;
    }
  }

  removeObject(name: string): void {
    const obj = this.objects.get(name);
    if (obj) {
      this.scene.remove(obj);
      this.objects.delete(name);
      this.animatedObjects = this.animatedObjects.filter((a) => a.mesh !== obj);
    }
  }

  updateEnvironment(settings: EnvironmentSettings): void {
    const sky = settings.sky_color;
    this.scene.background = new THREE.Color(sky.r, sky.g, sky.b);

    if (settings.fog_enabled && settings.fog_color) {
      const fogColor = new THREE.Color(
        settings.fog_color.r,
        settings.fog_color.g,
        settings.fog_color.b
      );
      this.scene.fog = new THREE.Fog(fogColor, settings.fog_near, settings.fog_far);
    } else {
      this.scene.fog = null;
    }

    const alc = settings.ambient_light_color;
    this.ambientLight.color.setRGB(alc.r, alc.g, alc.b);
    this.ambientLight.intensity = settings.ambient_light_intensity;

    const sc = settings.sun_color;
    this.sunLight.color.setRGB(sc.r, sc.g, sc.b);
    this.sunLight.intensity = settings.sun_intensity;
    this.sunLight.position.set(
      settings.sun_position.x,
      settings.sun_position.y,
      settings.sun_position.z
    );
  }

  addTerrain(params: TerrainParams): void {
    const size = params.size;
    const segments = params.segments;

    const geo = new THREE.PlaneGeometry(size, size, segments, segments);
    geo.rotateX(-Math.PI / 2);

    if (params.type === 'hills' || params.type === 'mountains') {
      const vertices = geo.attributes.position;
      const maxHeight = params.type === 'mountains' ? params.height : params.height * 0.5;
      const seed = params.seed ?? 42;

      for (let i = 0; i < vertices.count; i++) {
        const x = vertices.getX(i);
        const z = vertices.getZ(i);
        // Simple noise-like displacement
        const h =
          Math.sin(x * 0.05 + seed) * Math.cos(z * 0.05 + seed) * maxHeight +
          Math.sin(x * 0.1 + seed * 2) * Math.cos(z * 0.08 + seed * 2) * maxHeight * 0.5;
        vertices.setY(i, h);
      }
      geo.computeVertexNormals();
    }

    const color = params.color;
    let material: THREE.Material;

    if (params.type === 'water') {
      material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color.r, color.g, color.b),
        metalness: 0.1,
        roughness: 0.1,
        transparent: true,
        opacity: 0.7,
      });
    } else {
      material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color.r, color.g, color.b),
        roughness: 0.9,
        flatShading: params.type === 'mountains',
      });
    }

    const mesh = new THREE.Mesh(geo, material);
    mesh.receiveShadow = true;
    this.scene.add(mesh);
    this.objects.set(`__terrain_${this.objects.size}`, mesh);
  }
}
