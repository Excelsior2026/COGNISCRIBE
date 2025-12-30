import { useState } from "react"

const emptySummary = {
  objectives: "",
  concepts: "",
  terms: "",
  procedures: "",
  summary: "",
}

const normalizeHeading = (heading) => {
  return heading
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim()
}

const mapHeadingToKey = (heading) => {
  const normalized = normalizeHeading(heading)
  if (normalized.includes("learning objective")) return "objectives"
  if (normalized.includes("core concept")) return "concepts"
  if (normalized.includes("clinical term") || normalized === "terms") return "terms"
  if (normalized.includes("procedure") || normalized.includes("protocol")) return "procedures"
  if (normalized.endsWith("summary") || normalized === "summary") return "summary"
  return null
}

const parseSummarySections = (text) => {
  const sections = { ...emptySummary }
  if (!text) return sections

  const matches = Array.from(text.matchAll(/^\s*#{2,4}\s*(.+?)\s*$/gm))
  if (matches.length === 0) {
    sections.summary = text.trim()
    return sections
  }

  for (let i = 0; i < matches.length; i += 1) {
    const heading = matches[i][1]
    const key = mapHeadingToKey(heading)
    const start = matches[i].index + matches[i][0].length
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length
    const content = text.slice(start, end).trim()
    if (key && content) {
      sections[key] = content
    }
  }

  if (!Object.values(sections).some(Boolean)) {
    sections.summary = text.trim()
  }

  return sections
}

const getSummary = (data) => {
  if (data?.summary && typeof data.summary === "object") {
    return data.summary
  }

  const raw = typeof data?.summary === "string"
    ? data.summary
    : (typeof data?.summary_text === "string" ? data.summary_text : "")

  return parseSummarySections(raw)
}

const getTranscription = (data) => {
  if (data?.transcription) {
    return data.transcription
  }
  if (data?.transcript?.text) {
    return data.transcript.text
  }
  return ""
}

export default function ResultsPanel({ data }) {
  const [copiedSection, setCopiedSection] = useState(null)
  const [expandedSections, setExpandedSections] = useState({
    objectives: true,
    concepts: true,
    terms: true,
    procedures: true,
    summary: true,
  })
  const summary = getSummary(data)
  const transcription = getTranscription(data)

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const copyToClipboard = async (text, section) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedSection(section)
      setTimeout(() => setCopiedSection(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadAsMarkdown = () => {
    let markdown = `# Study Notes\n\n`
    markdown += `**Generated:** ${new Date().toLocaleDateString()}\n\n`
    
    if (summary.objectives) {
      markdown += `## 🎯 Learning Objectives\n\n${summary.objectives}\n\n`
    }
    if (summary.concepts) {
      markdown += `## 💡 Core Concepts\n\n${summary.concepts}\n\n`
    }
    if (summary.terms) {
      markdown += `## 📚 Clinical Terms & Definitions\n\n${summary.terms}\n\n`
    }
    if (summary.procedures) {
      markdown += `## ⚖️ Procedures & Protocols\n\n${summary.procedures}\n\n`
    }
    if (summary.summary) {
      markdown += `## 📝 Summary\n\n${summary.summary}\n\n`
    }
    if (transcription) {
      markdown += `## 🗣️ Full Transcription\n\n${transcription}\n\n`
    }

    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cogniscribe-notes-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const Section = ({ title, content, icon, sectionKey, color = "blue" }) => {
    if (!content) return null
    
    const isExpanded = expandedSections[sectionKey]
    const colorClasses = {
      blue: "border-blue-200 bg-blue-50",
      teal: "border-teal-200 bg-teal-50",
      purple: "border-purple-200 bg-purple-50",
      green: "border-green-200 bg-green-50",
      orange: "border-orange-200 bg-orange-50",
    }

    return (
      <div className={`border-2 rounded-xl overflow-hidden ${colorClasses[color]}`}>
        <div 
          onClick={() => toggleSection(sectionKey)}
          className="flex items-center justify-between p-4 cursor-pointer hover:opacity-80 transition-opacity"
        >
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <span>{icon}</span>
            {title}
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                copyToClipboard(content, sectionKey)
              }}
              className="p-2 hover:bg-white rounded-lg transition-colors"
              title="Copy to clipboard"
            >
              {copiedSection === sectionKey ? '✅' : '📋'}
            </button>
            <span className="text-gray-600">
              {isExpanded ? '▲' : '▼'}
            </span>
          </div>
        </div>
        
        {isExpanded && (
          <div className="p-4 pt-0">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                {content}
              </p>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-6 border-b border-gray-200">
        <div>
          <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
            <span>✨</span>
            Your Study Notes
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Generated on {new Date().toLocaleString()}
          </p>
        </div>
        <button
          onClick={downloadAsMarkdown}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-md"
        >
          <span>📥</span>
          Download
        </button>
      </div>

      {/* Sections */}
      <div className="space-y-4">
        <Section 
          title="Learning Objectives"
          content={summary.objectives}
          icon="🎯"
          sectionKey="objectives"
          color="blue"
        />
        
        <Section 
          title="Core Concepts"
          content={summary.concepts}
          icon="💡"
          sectionKey="concepts"
          color="teal"
        />
        
        <Section 
          title="Clinical Terms & Definitions"
          content={summary.terms}
          icon="📚"
          sectionKey="terms"
          color="purple"
        />
        
        <Section 
          title="Procedures & Protocols"
          content={summary.procedures}
          icon="⚖️"
          sectionKey="procedures"
          color="green"
        />
        
        <Section 
          title="Summary"
          content={summary.summary}
          icon="📝"
          sectionKey="summary"
          color="orange"
        />
      </div>

      {/* Full Transcription */}
      {transcription && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <details className="group">
            <summary className="cursor-pointer list-none flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <span className="text-lg font-bold text-gray-800 flex items-center gap-2">
                <span>🗣️</span>
                Full Transcription
              </span>
              <span className="text-gray-600 group-open:rotate-180 transition-transform">
                ▼
              </span>
            </summary>
            <div className="mt-4 p-6 bg-gray-50 rounded-lg">
              <div className="bg-white rounded-lg p-4 shadow-sm max-h-96 overflow-y-auto">
                <p className="text-gray-700 text-sm whitespace-pre-wrap leading-relaxed font-mono">
                  {transcription}
                </p>
              </div>
              <button
                onClick={() => copyToClipboard(transcription, 'transcription')}
                className="mt-4 flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
              >
                {copiedSection === 'transcription' ? '✅ Copied!' : '📋 Copy Transcription'}
              </button>
            </div>
          </details>
        </div>
      )}

      {/* Success Message */}
      <div className="mt-8 p-4 bg-green-50 border-2 border-green-200 rounded-xl text-center">
        <p className="text-green-800 font-medium">
          ✅ Success! Your study notes are ready. Happy studying! 💪
        </p>
      </div>
    </div>
  )
}
