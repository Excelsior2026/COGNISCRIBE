import {runPipeline} from "../api/pipeline"

export default function UploadCard({onResult}){
  return (
    <input type="file" onChange={async e=>{
      const res = await runPipeline(e.target.files[0])
      onResult(res)
    }}/>
  )
}
