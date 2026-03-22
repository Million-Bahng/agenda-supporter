interface Props {
  label: string
  value: number | string
  sub?: string
  color?: string
}

export default function StatCard({ label, value, sub, color = "bg-white" }: Props) {
  return (
    <div className={`${color} rounded-xl p-5 shadow-sm border border-gray-100`}>
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-3xl font-bold text-gray-800">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}
