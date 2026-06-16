import { useState, useCallback } from 'react'
import useSWR from 'swr'
import { get } from '../lib/api'
import { Badge } from '../components/Card'
import useWebSocket from '../lib/useWebSocket'

// Static hierarchy layout — positions in a 600×460 SVG viewport
const NODES = [
  { id: 'executive',     icon: '🧠', label: 'Executive',    x: 300, y: 50,  color: '#a78bfa', parent: null },
  { id: 'planner',       icon: '📋', label: 'Planner',      x: 140, y: 150, color: '#60a5fa', parent: 'executive' },
  { id: 'researcher',    icon: '🔍', label: 'Research',     x: 300, y: 150, color: '#34d399', parent: 'executive' },
  { id: 'monitor',       icon: '📡', label: 'Monitor',      x: 460, y: 150, color: '#f59e0b', parent: 'executive' },
  { id: 'bounty_hunter', icon: '🎯', label: 'Bounty',       x: 80,  y: 270, color: '#ef4444', parent: 'planner' },
  { id: 'reward_scout',  icon: '💰', label: 'Revenue',      x: 220, y: 270, color: '#22c55e', parent: 'researcher' },
  { id: 'builder',       icon: '🔨', label: 'Builder',      x: 360, y: 270, color: '#f97316', parent: 'researcher' },
  { id: 'browser',       icon: '🌐', label: 'Browser',      x: 80,  y: 390, color: '#06b6d4', parent: 'bounty_hunter' },
  { id: 'memory_agent',  icon: '🧩', label: 'Memory',       x: 220, y: 390, color: '#8b5cf6', parent: 'reward_scout' },
  { id: 'telegram_agent',icon: '📱', label: 'Social',       x: 360, y: 390, color: '#2563eb', parent: 'builder' },
  { id: 'executor',      icon: '⚙️', label: 'Executor',     x: 500, y: 390, color: '#64748b', parent: 'monitor' },
]

const EDGES = NODES.filter(n => n.parent).map(n => {
  const parent = NODES.find(p => p.id === n.parent)
  return { from: parent, to: n, id: `${n.parent}->${n.id}` }
})

const STATUS_PULSE = { running: true }

function AgentNode({ node, taskStatus, taskPrompt, onClick, selected }) {
  const isRunning = taskStatus === 'running'
  const isFailed = taskStatus === 'failed'
  const color = isFailed ? '#ef4444' : isRunning ? '#60a5fa' : node.color

  return (
    <g
      onClick={() => onClick(node)}
      style={{ cursor: 'pointer' }}
      role="button"
      aria-label={node.label}
    >
      {/* Glow ring when running */}
      {isRunning && (
        <circle
          cx={node.x}
          cy={node.y}
          r={32}
          fill="none"
          stroke={color}
          strokeWidth={2}
          opacity={0.3}
          style={{ animation: 'pulse-ring 1.5s ease-in-out infinite' }}
        />
      )}
      {/* Main circle */}
      <circle
        cx={node.x}
        cy={node.y}
        r={26}
        fill={selected ? color : 'var(--surface2)'}
        stroke={color}
        strokeWidth={selected ? 3 : isRunning ? 2 : 1.5}
        style={{ filter: isRunning ? `drop-shadow(0 0 6px ${color})` : 'none' }}
      />
      {/* Icon */}
      <text x={node.x} y={node.y - 2} textAnchor="middle" dominantBaseline="middle" fontSize={18} style={{ userSelect: 'none' }}>
        {node.icon}
      </text>
      {/* Label */}
      <text x={node.x} y={node.y + 40} textAnchor="middle" fontSize={10} fill="var(--muted)" style={{ userSelect: 'none' }}>
        {node.label}
      </text>
      {/* Status dot */}
      <circle
        cx={node.x + 20}
        cy={node.y - 20}
        r={5}
        fill={isRunning ? '#60a5fa' : isFailed ? '#ef4444' : '#22c55e'}
        style={{ filter: isRunning ? 'drop-shadow(0 0 3px #60a5fa)' : 'none' }}
      />
    </g>
  )
}

export default function WarMapPage() {
  const { data: agents = [] } = useSWR('/agents', get, { refreshInterval: 5000 })
  const { data: tasks = [] } = useSWR('/tasks', get, { refreshInterval: 3000 })
  const [selected, setSelected] = useState(null)
  const [wsConnected, setWsConnected] = useState(false)

  useWebSocket(useCallback((msg) => {
    setWsConnected(true)
  }, []))

  const taskList = Array.isArray(tasks) ? tasks : []

  // Build agent → current task map
  const agentTaskMap = {}
  for (const t of taskList) {
    if (!agentTaskMap[t.agent_id] || t.status === 'running') {
      agentTaskMap[t.agent_id] = t
    }
  }

  const recentTasks = taskList.slice(0, 10)
  const runningCount = taskList.filter(t => t.status === 'running').length
  const completedCount = taskList.filter(t => t.status === 'completed').length
  const failedCount = taskList.filter(t => t.status === 'failed').length

  const selectedTask = selected ? agentTaskMap[selected.id] : null

  return (
    <div style={{ padding: '20px 16px 100px', background: 'var(--bg)', minHeight: '100%' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 style={{ color: 'var(--text)', fontSize: '20px', fontWeight: 800 }}>🗺️ Agent War Map</h1>
          <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '2px' }}>
            Live operational command view
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div
            style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: wsConnected ? '#22c55e' : '#6b7280',
              boxShadow: wsConnected ? '0 0 6px #22c55e' : 'none',
            }}
            className={wsConnected ? 'animate-pulse' : ''}
          />
          <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
            {wsConnected ? 'Live' : 'Polling'}
          </span>
        </div>
      </div>

      {/* Stats strip */}
      <div className="flex gap-3 mb-4">
        {[
          { label: 'Running', value: runningCount, color: '#60a5fa' },
          { label: 'Completed', value: completedCount, color: '#22c55e' },
          { label: 'Failed', value: failedCount, color: '#ef4444' },
          { label: 'Agents', value: NODES.length, color: '#a78bfa' },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            style={{
              flex: 1, padding: '10px 8px', borderRadius: '12px', textAlign: 'center',
              background: 'var(--surface)', border: '1px solid var(--border)',
            }}
          >
            <p style={{ fontSize: '20px', fontWeight: 700, color }}>{value}</p>
            <p style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '2px' }}>{label}</p>
          </div>
        ))}
      </div>

      {/* SVG War Map */}
      <div
        style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: '20px', overflow: 'hidden', marginBottom: '16px',
        }}
      >
        <style>{`
          @keyframes pulse-ring {
            0%, 100% { r: 28; opacity: 0.3; }
            50% { r: 34; opacity: 0.1; }
          }
        `}</style>
        <svg
          viewBox="0 -10 600 470"
          width="100%"
          style={{ display: 'block', maxHeight: '420px' }}
          aria-label="Agent hierarchy map"
        >
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--border)" strokeWidth="0.5" opacity="0.5" />
            </pattern>
          </defs>
          <rect width="600" height="470" fill="url(#grid)" />

          {/* Edges */}
          {EDGES.map(({ from, to, id }) => {
            const fromTask = agentTaskMap[from.id]
            const toTask = agentTaskMap[to.id]
            const isActive = fromTask?.status === 'running' || toTask?.status === 'running'
            return (
              <line
                key={id}
                x1={from.x} y1={from.y + 26}
                x2={to.x} y2={to.y - 26}
                stroke={isActive ? '#60a5fa' : 'var(--border)'}
                strokeWidth={isActive ? 1.5 : 1}
                strokeDasharray={isActive ? '0' : '4 4'}
                opacity={isActive ? 0.8 : 0.4}
              />
            )
          })}

          {/* Nodes */}
          {NODES.map(node => {
            const task = agentTaskMap[node.id]
            return (
              <AgentNode
                key={node.id}
                node={node}
                taskStatus={task?.status}
                taskPrompt={task?.prompt}
                onClick={setSelected}
                selected={selected?.id === node.id}
              />
            )
          })}
        </svg>
      </div>

      {/* Selected agent detail */}
      {selected && (
        <div
          style={{
            background: 'var(--surface)', border: `1px solid ${selected.color}40`,
            borderRadius: '16px', padding: '16px', marginBottom: '16px',
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span style={{ fontSize: '24px' }}>{selected.icon}</span>
              <div>
                <p style={{ color: 'var(--text)', fontWeight: 700, fontSize: '15px' }}>{selected.label}</p>
                <p style={{ color: 'var(--muted)', fontSize: '11px' }}>{selected.id}</p>
              </div>
            </div>
            <button
              onClick={() => setSelected(null)}
              style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', fontSize: '18px' }}
            >
              ✕
            </button>
          </div>
          {selectedTask ? (
            <div>
              <Badge label={selectedTask.status} type={selectedTask.status === 'running' ? 'blue' : selectedTask.status === 'completed' ? 'green' : 'red'} />
              <p style={{ color: 'var(--text)', fontSize: '13px', marginTop: '8px', lineHeight: '1.5' }}>
                {selectedTask.prompt?.slice(0, 200) || 'No prompt recorded'}
              </p>
              {selectedTask.result?.answer && (
                <p style={{ color: 'var(--muted)', fontSize: '12px', marginTop: '6px', lineHeight: '1.5' }}>
                  {selectedTask.result.answer.slice(0, 300)}
                </p>
              )}
            </div>
          ) : (
            <p style={{ color: 'var(--muted)', fontSize: '13px' }}>No active task — agent idle</p>
          )}
        </div>
      )}

      {/* Task Queue */}
      <div
        style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: '20px', padding: '16px 20px',
        }}
      >
        <h2 style={{ color: 'var(--text)', fontSize: '14px', fontWeight: 700, marginBottom: '12px' }}>
          📋 Task Queue (last 10)
        </h2>
        {recentTasks.length === 0 ? (
          <p style={{ color: 'var(--muted)', fontSize: '13px', textAlign: 'center', padding: '16px 0' }}>
            No tasks yet
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {recentTasks.map((t, i) => (
              <div
                key={t.id || i}
                style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '10px 12px', borderRadius: '12px',
                  background: 'var(--surface2)', border: '1px solid var(--border)',
                }}
              >
                <span
                  style={{
                    width: '8px', height: '8px', borderRadius: '50%', flexShrink: 0,
                    background: t.status === 'completed' ? '#22c55e'
                      : t.status === 'running' ? '#60a5fa'
                      : t.status === 'failed' ? '#ef4444' : '#a78bfa',
                  }}
                  className={t.status === 'running' ? 'animate-pulse' : ''}
                />
                <span style={{ flex: 1, fontSize: '12px', color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.prompt?.slice(0, 60) || `Task #${t.id}`}
                </span>
                <div style={{ flexShrink: 0, display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <Badge label={t.agent_id} type="purple" />
                  <Badge label={t.status} type={t.status === 'running' ? 'blue' : t.status === 'completed' ? 'green' : t.status === 'failed' ? 'red' : 'gray'} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
