import {useState} from "react"
import UploadCard from "./components/UploadCard"
import ResultsPanel from "./components/ResultsPanel"

export default function App(){
  const [data,setData]=useState(null)
  return (
    <div className="max-w-4xl mx-auto p-8">
      <UploadCard onResult={setData}/>
      {data && <ResultsPanel data={data}/>}
    </div>
  )
}
