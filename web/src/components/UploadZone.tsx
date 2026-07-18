import { useCallback, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { FileText, UploadCloud, X } from 'lucide-react'

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']

interface UploadZoneProps {
  file: File | null
  onFileSelected: (file: File | null) => void
}

function isAccepted(file: File): boolean {
  const name = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

export function UploadZone({ file, onFileSelected }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      const picked = fileList?.[0]
      if (!picked) return
      if (!isAccepted(picked)) {
        setError(`Unsupported file type. Use ${ACCEPTED_EXTENSIONS.join(', ')}`)
        return
      }
      setError(null)
      onFileSelected(picked)
    },
    [onFileSelected],
  )

  return (
    <div>
      <motion.div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          handleFiles(e.dataTransfer.files)
        }}
        onClick={() => inputRef.current?.click()}
        animate={{
          borderColor: isDragging ? 'rgba(167,139,250,0.9)' : 'rgba(255,255,255,0.12)',
          scale: isDragging ? 1.01 : 1,
        }}
        className="glass-panel relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-8 py-12 text-center"
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        <AnimatePresence mode="wait">
          {file ? (
            <motion.div
              key="file"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex items-center gap-3 rounded-xl bg-white/5 px-4 py-3"
            >
              <FileText className="h-5 w-5 text-violet-400" />
              <span className="max-w-xs truncate text-sm text-zinc-200">{file.name}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onFileSelected(null)
                  if (inputRef.current) inputRef.current.value = ''
                }}
                className="ml-1 rounded-full p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex flex-col items-center gap-3"
            >
              <motion.div
                animate={{ y: isDragging ? -4 : 0 }}
                className="rounded-full bg-violet-500/10 p-4 text-violet-400"
              >
                <UploadCloud className="h-7 w-7" />
              </motion.div>
              <div>
                <p className="font-medium text-zinc-100">Drop your resume here</p>
                <p className="mt-1 text-sm text-zinc-500">or click to browse — PDF, DOCX, TXT, MD</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </div>
  )
}
