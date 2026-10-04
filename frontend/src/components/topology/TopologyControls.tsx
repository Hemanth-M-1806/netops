import React from 'react'
import { RotateCcw, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { useTopologyStore } from '@/stores/useTopologyStore'

export const TopologyControls: React.FC = () => {
  const { resetCamera } = useTopologyStore()

  return (
    <div className="absolute bottom-6 left-6 z-20 flex items-center gap-2 p-1.5 rounded-xl bg-surface-950/80 backdrop-blur-md border border-white/10 shadow-xl">
      <button
        onClick={resetCamera}
        title="Reset Camera View"
        className="p-2 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-white/5 transition-colors cursor-pointer"
      >
        <RotateCcw className="w-4 h-4" />
      </button>
      <div className="w-px h-4 bg-white/10" />
      <span className="text-[11px] font-mono text-slate-400 px-2">
        DRAG TO ROTATE • SCROLL TO ZOOM
      </span>
    </div>
  )
}
