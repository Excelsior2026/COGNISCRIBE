export default function ResultsPanel({ data }) {
  const { transcript, summary } = data || {}
  return (
    <div className="mt-6 space-y-4">
      <section>
        <h2 className="text-lg font-semibold mb-2">Summary</h2>
        <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded border">
          {summary}
        </pre>
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-2">Transcript</h2>
        <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded border text-sm max-h-96 overflow-auto">
          {transcript?.text}
        </pre>
      </section>
    </div>
  )
}
