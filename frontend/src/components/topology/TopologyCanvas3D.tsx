import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { useTopologyStore } from '@/stores/useTopologyStore'
import { useDevices } from '@/hooks/useDevices'
import { DEVICE_COORDINATES, KNOWN_LINKS } from '@/utils/constants'
import { DeviceDrawer } from './DeviceDrawer'
import { TopologyControls } from './TopologyControls'
import { getDeviceStatusColor } from '@/utils/formatters'
import { Device } from '@/types'

export const TopologyCanvas3D: React.FC<{ className?: string }> = ({
  className = 'h-full w-full',
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const { data: devicesData } = useDevices()
  const devices = devicesData?.items || []

  const {
    selectedDeviceId,
    hoveredDeviceId,
    selectDevice,
    setHoveredDeviceId,
    cameraResetTrigger,
  } = useTopologyStore()

  const [tooltip, setTooltip] = useState<{
    visible: boolean
    x: number
    y: number
    device: Device | null
  }>({ visible: false, x: 0, y: 0, device: null })

  const controlsRef = useRef<OrbitControls | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Scene
    const scene = new THREE.Scene()
    scene.background = null // Transparent for CSS radial gradient

    // Camera
    const camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    )
    camera.position.set(0, 5, 15)
    cameraRef.current = camera

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(container.clientWidth, container.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.maxDistance = 30
    controls.minDistance = 4
    controlsRef.current = controls

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
    scene.add(ambientLight)

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2)
    dirLight.position.set(10, 20, 15)
    scene.add(dirLight)

    const cyanLight = new THREE.PointLight(0x06b6d4, 1.5, 30)
    cyanLight.position.set(-10, -5, -5)
    scene.add(cyanLight)

    // Grid Floor
    const grid = new THREE.GridHelper(30, 30, 0x0284c7, 0x1e293b)
    grid.position.y = -5
    scene.add(grid)

    // Device Positions Mapping
    const positionsMap = new Map<string, [number, number, number]>()
    devices.forEach((d, idx) => {
      if (DEVICE_COORDINATES[d.hostname]) {
        positionsMap.set(d.hostname, DEVICE_COORDINATES[d.hostname])
      } else {
        const angle = (idx / Math.max(devices.length, 1)) * Math.PI * 2
        positionsMap.set(d.hostname, [Math.cos(angle) * 7, Math.sin(angle) * 3, 0])
      }
    })

    // Node objects and interactive mesh list for raycasting
    const interactiveMeshes: THREE.Mesh[] = []
    const meshToDeviceMap = new Map<THREE.Mesh, Device>()
    const ringMeshes: THREE.Mesh[] = []

    // Helper: Create geometry per device type
    const getGeometry = (type: string) => {
      switch (type) {
        case 'router':
          return new THREE.CylinderGeometry(0.9, 0.9, 0.4, 32)
        case 'switch':
          return new THREE.BoxGeometry(1.4, 0.5, 1.4)
        case 'firewall':
          return new THREE.OctahedronGeometry(0.9, 0)
        case 'access_point':
          return new THREE.SphereGeometry(0.7, 24, 24)
        default:
          return new THREE.DodecahedronGeometry(0.8, 0)
      }
    }

    // Build Device Nodes
    devices.forEach((device) => {
      const pos = positionsMap.get(device.hostname) || [0, 0, 0]
      const statusColors = getDeviceStatusColor(device.status)
      const color = new THREE.Color(statusColors.hex)

      // Main Mesh
      const geometry = getGeometry(device.device_type)
      const material = new THREE.MeshStandardMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.35,
        roughness: 0.2,
        metalness: 0.7,
      })

      const mesh = new THREE.Mesh(geometry, material)
      mesh.position.set(...pos)
      scene.add(mesh)

      interactiveMeshes.push(mesh)
      meshToDeviceMap.set(mesh, device)

      // Pulsing outer aura ring
      const ringGeo = new THREE.RingGeometry(1.2, 1.35, 32)
      const ringMat = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.35,
      })
      const ring = new THREE.Mesh(ringGeo, ringMat)
      ring.position.set(...pos)
      scene.add(ring)
      ringMeshes.push(ring)
    })

    // Build Links & Animated Packet Particles
    const particles: { mesh: THREE.Mesh; curve: THREE.QuadraticBezierCurve3; speed: number }[] = []

    KNOWN_LINKS.forEach((link) => {
      const p1 = positionsMap.get(link.source)
      const p2 = positionsMap.get(link.target)
      if (!p1 || !p2) return

      const v1 = new THREE.Vector3(...p1)
      const v2 = new THREE.Vector3(...p2)
      const mid = new THREE.Vector3().addVectors(v1, v2).multiplyScalar(0.5)
      mid.y += 0.8

      const curve = new THREE.QuadraticBezierCurve3(v1, mid, v2)
      const tubeGeo = new THREE.TubeGeometry(curve, 20, 0.04, 8, false)
      const tubeMat = new THREE.MeshBasicMaterial({
        color: 0x0284c7,
        transparent: true,
        opacity: 0.35,
      })
      const tube = new THREE.Mesh(tubeGeo, tubeMat)
      scene.add(tube)

      // Packet particle
      const pGeo = new THREE.SphereGeometry(0.12, 16, 16)
      const pMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
      const pMesh = new THREE.Mesh(pGeo, pMat)
      scene.add(pMesh)
      particles.push({ mesh: pMesh, curve, speed: 0.3 + Math.random() * 0.2 })
    })

    // Raycaster for Hover & Selection
    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()

    const onPointerMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / container.clientWidth) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / container.clientHeight) * 2 + 1

      raycaster.setFromCamera(mouse, camera)
      const intersects = raycaster.intersectObjects(interactiveMeshes)

      if (intersects.length > 0) {
        container.style.cursor = 'pointer'
        const hitMesh = intersects[0].object as THREE.Mesh
        const hitDevice = meshToDeviceMap.get(hitMesh)
        if (hitDevice) {
          setHoveredDeviceId(hitDevice.device_id)
          setTooltip({
            visible: true,
            x: e.clientX - rect.left,
            y: e.clientY - rect.top - 40,
            device: hitDevice,
          })
        }
      } else {
        container.style.cursor = 'auto'
        setHoveredDeviceId(null)
        setTooltip((prev) => ({ ...prev, visible: false }))
      }
    }

    const onPointerClick = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / container.clientWidth) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / container.clientHeight) * 2 + 1

      raycaster.setFromCamera(mouse, camera)
      const intersects = raycaster.intersectObjects(interactiveMeshes)

      if (intersects.length > 0) {
        const hitMesh = intersects[0].object as THREE.Mesh
        const hitDevice = meshToDeviceMap.get(hitMesh)
        if (hitDevice) {
          selectDevice(hitDevice.device_id)
        }
      }
    }

    container.addEventListener('mousemove', onPointerMove)
    container.addEventListener('click', onPointerClick)

    // Resize Handler
    const onResize = () => {
      if (!container) return
      camera.aspect = container.clientWidth / container.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(container.clientWidth, container.clientHeight)
    }
    window.addEventListener('resize', onResize)

    // Animation Loop
    let animationFrameId: number
    const clock = new THREE.Clock()

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)
      const delta = clock.getDelta()
      const elapsed = clock.getElapsedTime()

      // Rotate pulse rings
      ringMeshes.forEach((r) => {
        r.rotation.z += delta * 0.7
        r.rotation.x += delta * 0.3
      })

      // Move packet flow particles along curves
      particles.forEach((p) => {
        const t = (elapsed * p.speed) % 1
        p.mesh.position.copy(p.curve.getPointAt(t))
      })

      controls.update()
      renderer.render(scene, camera)
    }

    animate()

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', onResize)
      container.removeEventListener('mousemove', onPointerMove)
      container.removeEventListener('click', onPointerClick)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [devices])

  // Camera reset trigger
  useEffect(() => {
    if (controlsRef.current && cameraResetTrigger > 0) {
      controlsRef.current.reset()
    }
  }, [cameraResetTrigger])

  return (
    <div className={`relative ${className} overflow-hidden bg-surface-950 select-none`}>
      <div ref={containerRef} className="w-full h-full" />

      {/* Floating Hover Tooltip */}
      {tooltip.visible && tooltip.device && (
        <div
          className="absolute z-30 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-2 animate-in fade-in zoom-in-95 duration-100"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <div className="flex flex-col items-center">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-950/95 border border-white/20 backdrop-blur-md shadow-2xl">
              <span
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: getDeviceStatusColor(tooltip.device.status).hex,
                }}
              />
              <span className="font-mono font-bold text-xs text-white">
                {tooltip.device.hostname}
              </span>
              <span className="text-[10px] font-mono text-cyan-400 uppercase">
                {tooltip.device.device_type}
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400 mt-1 bg-surface-900/80 px-2 py-0.5 rounded">
              {tooltip.device.ip_address}
            </span>
          </div>
        </div>
      )}

      <TopologyControls />
      <DeviceDrawer />
    </div>
  )
}
