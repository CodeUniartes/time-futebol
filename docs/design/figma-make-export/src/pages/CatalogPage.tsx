import { useState, useRef, type ReactElement } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';
import { CATALOG_ITEMS, CATEGORY_LABELS, type Category, type CatalogItem } from '../data/mockData';

const CATEGORIES: Category[] = ['letras', 'fila', 'costas', 'frente', 'logos', 'camisa'];

export default function CatalogPage() {
  const navigate = useNavigate();
  const { team, season, version, cart, cartCount, addToCart, updateQuantity } = useApp();
  const [activeCategory, setActiveCategory] = useState<Category>('letras');
  const [nameInput, setNameInput] = useState('');
  const tabsRef = useRef<HTMLDivElement>(null);

  const filtered = CATALOG_ITEMS.filter((item) => item.category === activeCategory);

  function getQuantity(id: string) {
    return cart.find((c) => c.id === id)?.quantity ?? 0;
  }

  function handleAdd(item: CatalogItem) {
    addToCart({
      id: item.id,
      name: item.name,
      category: item.category,
      widthCm: item.widthCm,
      heightCm: item.heightCm,
    });
  }

  function handleAddName() {
    if (!nameInput.trim()) return;
    const name = nameInput.trim().toUpperCase();
    const id = `fila-custom-${name}`;
    addToCart({
      id,
      name: `Fila: ${name}`,
      category: 'fila',
      widthCm: Math.min(58, name.length * 5.4 + 4),
      heightCm: 8,
      customName: name,
    });
    setNameInput('');
  }

  function handleAddAllNames() {
    CATALOG_ITEMS.filter((i) => i.category === 'fila').forEach((item) => handleAdd(item));
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Sticky top selectors */}
      <div className="sticky top-14 z-30 bg-white border-b border-muted">
        <div className="max-w-screen-xl mx-auto px-4 py-2 flex items-center gap-2 overflow-x-auto scrollbar-none">
          {team && (
            <div className="flex items-center gap-1.5 bg-surface rounded-lg px-3 py-1.5 flex-shrink-0 border border-muted">
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ background: team.accentColor }}
              />
              <span className="text-xs font-semibold text-graphite whitespace-nowrap">{team.name}</span>
            </div>
          )}
          <ChipSelector value={season} />
          <ChipSelector value={version} />
          <button
            onClick={() => navigate('/')}
            className="text-xs text-orange font-semibold whitespace-nowrap focus-ring rounded-lg px-2 py-1.5 hover:bg-orange/5 transition-colors flex-shrink-0"
          >
            Alterar
          </button>
        </div>

        {/* Category tabs */}
        <div ref={tabsRef} className="flex overflow-x-auto scrollbar-none border-t border-muted/50">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`flex-shrink-0 px-4 py-2.5 text-[13px] font-semibold whitespace-nowrap transition-colors focus-ring border-b-2 ${
                activeCategory === cat
                  ? 'border-orange text-graphite'
                  : 'border-transparent text-subtle hover:text-graphite'
              }`}
            >
              {CATEGORY_LABELS[cat]}
            </button>
          ))}
        </div>
      </div>

      {/* Quick actions for fila */}
      {activeCategory === 'fila' && (
        <div className="max-w-screen-xl mx-auto px-4 pt-4 pb-2 space-y-3">
          <div className="p-4 rounded-[12px] bg-surface border border-muted">
            <p className="text-sm font-semibold text-graphite mb-2">Adicionar nome</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && handleAddName()}
                placeholder="Digite o nome (ex: RODRIGUES)"
                maxLength={14}
                className="flex-1 px-3 py-2 rounded-lg border border-muted bg-white text-sm text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors font-semibold tracking-wide"
              />
              <button
                onClick={handleAddName}
                disabled={!nameInput.trim()}
                className="px-4 py-2 bg-graphite text-white rounded-[10px] text-sm font-semibold disabled:opacity-40 hover:bg-graphite/90 active:scale-95 transition-all focus-ring"
              >
                Adicionar
              </button>
            </div>
          </div>
          <button
            onClick={handleAddAllNames}
            className="w-full py-2.5 rounded-[10px] border-2 border-graphite text-graphite text-sm font-semibold hover:bg-surface transition-colors focus-ring"
          >
            Adicionar fila completa
          </button>
        </div>
      )}

      {/* Item grid */}
      <div className="max-w-screen-xl mx-auto px-4 pt-4 pb-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {filtered.map((item) => {
            const qty = getQuantity(item.id);
            return (
              <div
                key={item.id}
                className="bg-white rounded-[12px] border border-muted overflow-hidden flex flex-col"
                style={{ boxShadow: '0 2px 8px rgba(69,72,73,0.08)' }}
              >
                {/* Art preview */}
                <div className="relative bg-[#F8F8F8] aspect-square flex items-center justify-center overflow-hidden">
                  <CheckeredBg />
                  {item.previewChar ? (
                    <span className="relative z-10 text-[48px] font-semibold italic text-graphite leading-none select-none">
                      {item.previewChar}
                    </span>
                  ) : (
                    <div className="relative z-10 flex flex-col items-center justify-center gap-1">
                      <ArtPlaceholderIcon category={item.category} />
                    </div>
                  )}
                  {qty > 0 && (
                    <div className="absolute top-2 right-2 z-20 bg-orange text-white text-[10px] font-semibold rounded-full w-5 h-5 flex items-center justify-center">
                      {qty}
                    </div>
                  )}
                </div>

                {/* Info + stepper */}
                <div className="p-2.5 flex flex-col gap-2 flex-1">
                  <div className="flex-1">
                    <p className="text-[12px] font-semibold text-graphite leading-tight line-clamp-2">{item.name}</p>
                    <p className="text-[11px] text-subtle mt-0.5">
                      {item.widthCm.toLocaleString('pt-BR', { minimumFractionDigits: 1 })} × {item.heightCm.toLocaleString('pt-BR', { minimumFractionDigits: 1 })} cm
                    </p>
                  </div>

                  {qty === 0 ? (
                    <button
                      onClick={() => handleAdd(item)}
                      className="w-full py-1.5 bg-graphite text-white text-[12px] font-semibold rounded-[8px] hover:bg-graphite/90 active:scale-95 transition-all focus-ring"
                    >
                      Adicionar
                    </button>
                  ) : (
                    <div className="flex items-center justify-between bg-surface rounded-[8px] h-8">
                      <button
                        onClick={() => updateQuantity(item.id, qty - 1)}
                        className="w-8 h-8 flex items-center justify-center text-graphite font-semibold text-lg hover:bg-muted rounded-l-[8px] transition-colors focus-ring"
                        aria-label="Diminuir"
                      >
                        −
                      </button>
                      <span className="text-[13px] font-semibold text-graphite w-6 text-center">{qty}</span>
                      <button
                        onClick={() => updateQuantity(item.id, qty + 1)}
                        className="w-8 h-8 flex items-center justify-center text-graphite font-semibold text-lg hover:bg-muted rounded-r-[8px] transition-colors focus-ring"
                        aria-label="Aumentar"
                      >
                        +
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Sticky bottom bar */}
      {cartCount > 0 && (
        <div className="fixed bottom-16 left-0 right-0 z-30 px-4 pb-2">
          <div className="max-w-screen-xl mx-auto">
            <button
              onClick={() => navigate('/order')}
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] flex items-center justify-center gap-3 hover:bg-graphite/90 active:scale-[0.98] transition-all focus-ring"
              style={{ boxShadow: '0 4px 16px rgba(69,72,73,0.25)' }}
            >
              <span
                className="bg-orange text-white text-xs font-semibold rounded-full min-w-[22px] h-[22px] flex items-center justify-center px-1.5"
              >
                {cartCount}
              </span>
              Ver pedido
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ChipSelector({ value }: { value: string }) {
  return (
    <div className="flex-shrink-0 bg-surface rounded-lg px-3 py-1.5 border border-muted">
      <span className="text-xs font-semibold text-graphite whitespace-nowrap">{value}</span>
    </div>
  );
}

function CheckeredBg() {
  return (
    <div
      className="absolute inset-0"
      style={{
        backgroundImage:
          'linear-gradient(45deg, #e8e8e8 25%, transparent 25%), linear-gradient(-45deg, #e8e8e8 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #e8e8e8 75%), linear-gradient(-45deg, transparent 75%, #e8e8e8 75%)',
        backgroundSize: '12px 12px',
        backgroundPosition: '0 0, 0 6px, 6px -6px, -6px 0px',
        opacity: 0.5,
      }}
    />
  );
}

function ArtPlaceholderIcon({ category }: { category: Category }) {
  const icons: Record<Category, ReactElement> = {
    letras: <span className="text-3xl font-semibold italic text-muted">A</span>,
    fila: <span className="text-lg font-semibold text-muted tracking-widest">ABC</span>,
    costas: <span className="text-3xl font-semibold text-muted">10</span>,
    frente: <span className="text-xl font-semibold text-muted">9</span>,
    logos: (
      <svg className="w-10 h-10 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="12" cy="12" r="4" />
      </svg>
    ),
    camisa: (
      <svg className="w-12 h-12 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.2}>
        <path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.57a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.57a2 2 0 0 0-1.34-2.23z" />
      </svg>
    ),
  };
  return icons[category] ?? null;
}
