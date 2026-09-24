import { useState, useRef } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';

const MAX_SIZE_MB = 20;
const ACCEPTED = ['image/png', 'image/jpeg', 'application/pdf'];
const FILM_WIDTH_CM = 58;

export default function AddArtPage() {
  const navigate = useNavigate();
  const { addToCart } = useApp();

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [widthCm, setWidthCm] = useState('');
  const [heightCm, setHeightCm] = useState('');
  const [lockRatio, setLockRatio] = useState(true);
  const [naturalRatio, setNaturalRatio] = useState<number | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function processFile(f: File) {
    setError('');
    if (!ACCEPTED.includes(f.type)) {
      setError('Formato inválido. Use PNG, JPG ou PDF.');
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Arquivo muito grande. Máximo ${MAX_SIZE_MB} MB.`);
      return;
    }
    setFile(f);
    if (f.type !== 'application/pdf') {
      const url = URL.createObjectURL(f);
      setPreview(url);
      const img = new Image();
      img.onload = () => {
        const ratio = img.width / img.height;
        setNaturalRatio(ratio);
        const defaultW = Math.min(20, FILM_WIDTH_CM);
        setWidthCm(defaultW.toFixed(1));
        setHeightCm((defaultW / ratio).toFixed(1));
      };
      img.src = url;
    } else {
      setPreview(null);
      setNaturalRatio(null);
      setWidthCm('20.0');
      setHeightCm('20.0');
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) processFile(f);
  }

  function handleWidthChange(v: string) {
    setWidthCm(v);
    if (lockRatio && naturalRatio && v) {
      const w = parseFloat(v);
      if (!isNaN(w)) setHeightCm((w / naturalRatio).toFixed(1));
    }
  }

  function handleHeightChange(v: string) {
    setHeightCm(v);
    if (lockRatio && naturalRatio && v) {
      const h = parseFloat(v);
      if (!isNaN(h)) setWidthCm((h * naturalRatio).toFixed(1));
    }
  }

  function handleAdd() {
    const w = parseFloat(widthCm);
    const h = parseFloat(heightCm);
    if (!file || !agreed || isNaN(w) || isNaN(h) || w <= 0 || h <= 0) return;
    if (w > FILM_WIDTH_CM) {
      setError(`A largura máxima é ${FILM_WIDTH_CM} cm.`);
      return;
    }
    addToCart({
      id: `custom-${Date.now()}`,
      name: file.name.replace(/\.[^.]+$/, ''),
      category: 'logos',
      widthCm: w,
      heightCm: h,
    });
    navigate('/catalog');
  }

  const canAdd = !!file && agreed && !!widthCm && !!heightCm;

  return (
    <div className="max-w-screen-sm mx-auto px-4 py-6">
      <h1 className="text-[22px] font-semibold italic text-graphite mb-1">Enviar minha arte</h1>
      <p className="text-sm text-subtle mb-6">PNG, JPG ou PDF · Máximo {MAX_SIZE_MB} MB · Largura máxima {FILM_WIDTH_CM} cm</p>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative rounded-[12px] border-2 border-dashed cursor-pointer transition-colors flex flex-col items-center justify-center py-10 px-6 text-center mb-4 ${
          dragging ? 'border-orange bg-orange/5' : file ? 'border-graphite bg-surface' : 'border-muted hover:border-graphite hover:bg-surface/50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.pdf"
          className="sr-only"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) processFile(f); }}
        />
        {preview ? (
          <div className="w-full">
            <img
              src={preview}
              alt="Prévia da arte"
              className="max-h-48 mx-auto object-contain rounded-lg"
            />
            <p className="text-xs text-subtle mt-2 truncate px-4">{file?.name}</p>
            <p className="text-xs text-orange font-semibold mt-1">Clique para trocar</p>
          </div>
        ) : (
          <>
            <UploadIcon />
            <p className="text-sm font-semibold text-graphite mt-3">
              {file ? file.name : 'Arraste seu arquivo aqui'}
            </p>
            <p className="text-xs text-subtle mt-1">ou clique para selecionar</p>
          </>
        )}
      </div>

      {error && (
        <div className="flex gap-2 items-start p-3 bg-red-50 border border-red-200 rounded-[10px] mb-4">
          <ErrorIcon />
          <p className="text-sm text-red-700 font-semibold">{error}</p>
        </div>
      )}

      {/* Size inputs */}
      {file && (
        <div className="mb-4 p-4 bg-surface rounded-[12px] border border-muted space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-graphite">Tamanho de impressão</p>
            <button
              onClick={() => setLockRatio((v) => !v)}
              className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg transition-colors focus-ring ${lockRatio ? 'bg-orange/10 text-dark-orange' : 'bg-white border border-muted text-subtle hover:text-graphite'}`}
            >
              {lockRatio ? <LockIcon /> : <UnlockIcon />}
              {lockRatio ? 'Proporção travada' : 'Proporção livre'}
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-subtle font-semibold uppercase tracking-wide mb-1">Largura (cm)</label>
              <input
                type="number"
                min={0.1}
                max={FILM_WIDTH_CM}
                step={0.1}
                value={widthCm}
                onChange={(e) => handleWidthChange(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border border-muted rounded-[10px] text-[15px] text-graphite focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-subtle font-semibold uppercase tracking-wide mb-1">Altura (cm)</label>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={heightCm}
                onChange={(e) => handleHeightChange(e.target.value)}
                className="w-full px-3 py-2.5 bg-white border border-muted rounded-[10px] text-[15px] text-graphite focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
              />
            </div>
          </div>
          {parseFloat(widthCm) > FILM_WIDTH_CM && (
            <p className="text-xs text-orange font-semibold">
              ⚠ Largura excede o filme ({FILM_WIDTH_CM} cm). Reduza para continuar.
            </p>
          )}
        </div>
      )}

      {/* Responsibility checkbox */}
      {file && (
        <label className="flex items-start gap-3 cursor-pointer p-4 bg-surface rounded-[12px] border border-muted mb-6">
          <div className="relative flex-shrink-0 mt-0.5">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="sr-only"
            />
            <div className={`w-5 h-5 rounded-[5px] border-2 flex items-center justify-center transition-colors ${agreed ? 'bg-graphite border-graphite' : 'bg-white border-muted'}`}>
              {agreed && (
                <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </div>
          </div>
          <p className="text-[13px] text-graphite leading-relaxed">
            <span className="font-semibold">Li e concordo:</span> a qualidade da arte (fundo, resolução, cores) é de minha responsabilidade.
          </p>
        </label>
      )}

      <button
        onClick={handleAdd}
        disabled={!canAdd}
        className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] disabled:opacity-40 hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring"
      >
        {file ? 'Adicionar ao pedido' : 'Selecione um arquivo'}
      </button>
    </div>
  );
}

function UploadIcon() {
  return (
    <svg className="w-10 h-10 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function LockIcon() {
  return <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>;
}

function UnlockIcon() {
  return <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 9.9-1" /></svg>;
}
