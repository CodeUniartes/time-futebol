import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';
import { CATEGORY_LABELS } from '../data/mockData';

const FILM_WIDTH_CM = 58;
const FILM_PAGE_HEIGHT_CM = 200;
const DISPLAY_WIDTH_PX = 220;
const SCALE = DISPLAY_WIDTH_PX / FILM_WIDTH_CM;
const RULER_WIDTH = 32;
const GAP_CM = 0.5;

interface PackedItem {
  id: string;
  name: string;
  widthCm: number;
  heightCm: number;
  x: number;
  y: number;
  rotated: boolean;
  page: number;
}

function packItems(
  items: { id: string; name: string; widthCm: number; heightCm: number; quantity: number }[]
): PackedItem[] {
  const expanded: { id: string; name: string; w: number; h: number }[] = [];
  items.forEach((item) => {
    for (let i = 0; i < item.quantity; i++) {
      const fits = item.widthCm <= FILM_WIDTH_CM;
      const fitsRotated = item.heightCm <= FILM_WIDTH_CM;
      const rotated = !fits && fitsRotated;
      expanded.push({
        id: `${item.id}-${i}`,
        name: item.name,
        w: rotated ? item.heightCm : item.widthCm,
        h: rotated ? item.widthCm : item.heightCm,
      });
    }
  });

  const packed: PackedItem[] = [];
  let curX = 0;
  let curY = 0;
  let rowH = 0;
  let page = 0;

  for (const item of expanded) {
    if (item.w > FILM_WIDTH_CM) continue;

    if (curX + item.w > FILM_WIDTH_CM) {
      curX = 0;
      curY += rowH + GAP_CM;
      rowH = 0;
    }

    if (curY + item.h > FILM_PAGE_HEIGHT_CM) {
      curX = 0;
      curY = 0;
      rowH = 0;
      page++;
    }

    packed.push({
      id: item.id,
      name: item.name,
      widthCm: item.w,
      heightCm: item.h,
      x: curX,
      y: curY,
      rotated: false,
      page,
    });

    curX += item.w + GAP_CM;
    if (item.h > rowH) rowH = item.h;
  }

  return packed;
}

export default function OrderPage() {
  const navigate = useNavigate();
  const { cart, team, season, version, notes, updateQuantity, removeFromCart, setNotes, isLoggedIn, cartCount } = useApp();
  const [currentPage, setCurrentPage] = useState(0);

  const packed = useMemo(() => packItems(cart), [cart]);
  const totalPages = packed.length > 0 ? Math.max(...packed.map((p) => p.page)) + 1 : 0;
  const pagePacked = packed.filter((p) => p.page === currentPage);
  const usedHeightCm = pagePacked.length > 0
    ? Math.max(...pagePacked.map((p) => p.y + p.heightCm))
    : 0;
  const totalLengthCm = packed.length > 0
    ? (Math.max(...packed.map((p) => p.page)) * FILM_PAGE_HEIGHT_CM) +
      Math.max(...packed.filter((p) => p.page === totalPages - 1).map((p) => p.y + p.heightCm))
    : 0;

  const displayHeight = Math.max(150, usedHeightCm * SCALE + 20);

  const oversized = cart.filter(
    (c) => c.widthCm > FILM_WIDTH_CM && c.heightCm > FILM_WIDTH_CM
  );

  if (cart.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16 text-center">
        <div className="w-20 h-20 rounded-full bg-surface flex items-center justify-center mb-4">
          <CartEmptyIcon />
        </div>
        <h2 className="text-xl font-semibold italic text-graphite mb-2">Seu pedido está vazio</h2>
        <p className="text-subtle text-sm mb-6">Adicione estampas no catálogo para montar seu pedido.</p>
        <button
          onClick={() => navigate('/catalog')}
          className="bg-graphite text-white px-6 py-3 rounded-[10px] font-semibold text-[15px] hover:bg-graphite/90 transition-colors focus-ring"
        >
          Ir ao catálogo
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-screen-xl mx-auto">
      {/* Desktop: 3-zone; tablet: 2-col; mobile: stacked */}
      <div className="flex flex-col lg:flex-row min-h-screen">
        {/* Zone 1 – Cart list */}
        <div className="flex-1 lg:max-w-sm xl:max-w-md px-4 pt-4 pb-4 border-r border-muted/0 lg:border-muted overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-[20px] font-semibold italic text-graphite">Seu pedido</h1>
            <span className="text-sm text-subtle">{cartCount} peça{cartCount !== 1 ? 's' : ''}</span>
          </div>

          {team && (
            <div className="flex items-center gap-2 mb-4 p-3 bg-surface rounded-[10px] border border-muted">
              <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: team.accentColor }} />
              <span className="text-sm font-semibold text-graphite">{team.name}</span>
              <span className="text-xs text-subtle ml-1">{season} · {version}</span>
            </div>
          )}

          <div className="space-y-2 mb-4">
            {cart.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-[10px] border border-muted p-3 flex items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-graphite truncate">{item.name}</p>
                  <p className="text-[11px] text-subtle mt-0.5">
                    {CATEGORY_LABELS[item.category]} · {item.widthCm}×{item.heightCm}cm
                  </p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    className="w-7 h-7 flex items-center justify-center text-graphite font-semibold hover:bg-surface rounded-lg transition-colors focus-ring text-base"
                  >
                    {item.quantity === 1 ? <TrashIcon /> : '−'}
                  </button>
                  <span className="w-6 text-center text-[13px] font-semibold text-graphite">{item.quantity}</span>
                  <button
                    onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    className="w-7 h-7 flex items-center justify-center text-graphite font-semibold hover:bg-surface rounded-lg transition-colors focus-ring text-base"
                  >
                    +
                  </button>
                </div>
                <button
                  onClick={() => removeFromCart(item.id)}
                  className="p-1 text-subtle hover:text-graphite focus-ring rounded-lg transition-colors"
                  aria-label="Remover item"
                >
                  <TrashIcon />
                </button>
              </div>
            ))}
          </div>

          {/* Observação */}
          <div className="mb-4">
            <label className="block text-xs font-semibold text-subtle uppercase tracking-wide mb-1.5">
              Observação
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Alguma instrução especial para a produção..."
              rows={3}
              className="w-full px-3 py-2.5 rounded-[10px] border border-muted bg-surface text-sm text-graphite placeholder:text-subtle resize-none focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
            />
          </div>

          {/* Finalize */}
          <button
            onClick={() => navigate(isLoggedIn ? '/order-sent' : '/signup')}
            className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] hover:bg-graphite/90 active:scale-[0.98] transition-all focus-ring"
          >
            {isLoggedIn ? 'Finalizar pedido' : 'Entrar e finalizar'}
          </button>
          {!isLoggedIn && (
            <p className="text-center text-xs text-subtle mt-2">
              Você precisará criar uma conta ou entrar.
            </p>
          )}
        </div>

        {/* Zone 2 – Print panel preview */}
        <div className="flex-1 px-4 py-4 bg-surface/50">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-[16px] font-semibold italic text-graphite">Prévia do painel</h2>
            <div className="flex items-center gap-2 text-xs text-subtle">
              <span>Pinch para zoom</span>
              <PinchIcon />
            </div>
          </div>

          {oversized.length > 0 && (
            <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-[10px] flex gap-2">
              <WarningIcon />
              <div>
                <p className="text-xs font-semibold text-yellow-800">Arte maior que o filme (58cm)</p>
                {oversized.map((i) => (
                  <p key={i.id} className="text-xs text-yellow-700 mt-0.5">{i.name}</p>
                ))}
              </div>
            </div>
          )}

          {/* Film visual */}
          <div className="overflow-x-auto pb-2">
            <div className="flex gap-0 bg-white rounded-[12px] border border-muted overflow-hidden inline-flex" style={{ boxShadow: '0 2px 8px rgba(69,72,73,0.10)' }}>
              {/* Ruler */}
              <div
                className="bg-surface border-r border-muted flex-shrink-0 relative"
                style={{ width: RULER_WIDTH, height: displayHeight + 24 }}
              >
                <div className="pt-6">
                  {Array.from({ length: Math.ceil(usedHeightCm / 5) + 1 }).map((_, i) => (
                    <div key={i} style={{ position: 'absolute', top: 24 + i * 5 * SCALE }}>
                      <div className="absolute right-0 top-0 w-2.5 h-px bg-muted" />
                      <span className="absolute right-4 top-0 -translate-y-1/2 text-[8px] text-subtle leading-none">
                        {i * 5}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="absolute top-1 left-0 right-0 text-center">
                  <span className="text-[7px] text-subtle font-semibold">cm</span>
                </div>
              </div>

              {/* Film area */}
              <div className="flex-shrink-0 relative" style={{ width: DISPLAY_WIDTH_PX }}>
                {/* Header */}
                <div
                  className="bg-graphite/5 border-b border-muted flex items-center justify-center"
                  style={{ height: 24 }}
                >
                  <span className="text-[9px] font-semibold text-subtle">58 cm</span>
                </div>
                {/* Film body */}
                <div className="relative overflow-hidden" style={{ width: DISPLAY_WIDTH_PX, height: displayHeight }}>
                  <div className="absolute inset-0 bg-white" />
                  {pagePacked.map((item) => (
                    <div
                      key={item.id}
                      className="absolute border border-orange/40 rounded-[2px] flex items-center justify-center overflow-hidden"
                      style={{
                        left: item.x * SCALE,
                        top: item.y * SCALE,
                        width: item.widthCm * SCALE,
                        height: item.heightCm * SCALE,
                        background: 'rgba(244,119,38,0.06)',
                      }}
                      title={item.name}
                    >
                      <span className="text-[7px] text-orange/70 font-semibold text-center px-1 leading-tight truncate">
                        {item.name.length > 12 ? item.name.slice(0, 11) + '…' : item.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Page controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-3">
              <button
                onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                className="px-3 py-1.5 text-sm font-semibold text-graphite border border-muted rounded-[8px] disabled:opacity-40 hover:bg-surface focus-ring transition-colors"
              >
                ← Anterior
              </button>
              <span className="text-sm font-semibold text-subtle">
                Página {currentPage + 1} de {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage === totalPages - 1}
                className="px-3 py-1.5 text-sm font-semibold text-graphite border border-muted rounded-[8px] disabled:opacity-40 hover:bg-surface focus-ring transition-colors"
              >
                Próxima →
              </button>
            </div>
          )}

          {/* Summary */}
          <div className="mt-3 p-3 bg-white rounded-[10px] border border-muted">
            <p className="text-sm font-semibold text-graphite">
              Comprimento usado:{' '}
              <span className="text-orange">
                {(totalLengthCm / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2 })} m
              </span>{' '}
              · {packed.length} arte{packed.length !== 1 ? 's' : ''} em {totalPages} página{totalPages !== 1 ? 's' : ''}
            </p>
            <p className="text-[11px] text-subtle mt-1">
              Prévia estimada. A produção final pode variar.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function TrashIcon() {
  return (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6" /><path d="M14 11v6" /><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}

function CartEmptyIcon() {
  return (
    <svg className="w-10 h-10 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <path d="M16 10a4 4 0 0 1-8 0" />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg className="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function PinchIcon() {
  return (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><path d="M8 11h6M11 8v6" />
    </svg>
  );
}
