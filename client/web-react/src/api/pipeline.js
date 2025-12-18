export async function runPipeline(file) {
  const fd = new FormData()
  fd.append("file", file)
  const r = await fetch("/api/pipeline", { method:"POST", body:fd })
  return r.json()
}
