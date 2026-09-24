import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';
import { TEAMS, SEASONS, VERSIONS, type Team } from '../data/mockData';

type Step = 'time' | 'ano' | 'versao';

export default function StartPage() {
  const navigate = useNavigate();
  const { team, season, version, setTeam, setSeason, setVersion } = useApp();
  const [modal, setModal] = useState<Step | null>(null);
  const [search, setSearch] = useState('');

  const localTeam = team;
  const localSeason = season;
  const localVersion = version;

  const filteredTeams = TEAMS.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.state.toLowerCase().includes(search.toLowerCase())
  );

  const canContinue = localTeam && localSeason && localVersion;

  function handleSelectTeam(t: Team) {
    setTeam(t);
    setModal(null);
    setSearch('');
  }

  function handleSelectSeason(s: string) {
    setSeason(s);
    setModal(null);
  }

  function handleSelectVersion(v: string) {
    setVersion(v);
    setModal(null);
  }

  const cards: { step: Step; label: string; value: string; placeholder: string }[] = [
    { step: 'time', label: 'Time', value: localTeam?.name ?? '', placeholder: 'Selecionar time' },
    { step: 'ano', label: 'Ano', value: localSeason, placeholder: 'Selecionar ano' },
    { step: 'versao', label: 'Versão', value: localVersion, placeholder: 'Selecionar versão' },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero header */}
      <div className="px-4 pt-10 pb-8 max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div
            className="flex items-center justify-center rounded-2xl bg-surface border border-muted"
            style={{ width: 52, height: 52 }}
          >
            <span className="text-[10px] font-semibold text-subtle leading-tight text-center px-1">Logo<br />Uniartes</span>
          </div>
          <div>
            <p className="text-xs text-subtle font-semibold uppercase tracking-widest">Uniartes Uniformes</p>
            <p className="text-sm font-semibold text-graphite">Pedido DTF</p>
          </div>
        </div>

        <h1 className="text-[28px] font-semibold italic text-graphite leading-tight mb-2">
          Monte seu pedido
        </h1>
        <p className="text-[15px] text-subtle leading-relaxed">
          Escolha o time, a temporada e a versão para ver o catálogo de estampas DTF.
        </p>
      </div>

      {/* Selection cards */}
      <div className="px-4 max-w-lg mx-auto space-y-3 pb-8">
        {cards.map(({ step, label, value, placeholder }) => (
          <button
            key={step}
            onClick={() => { setModal(step); setSearch(''); }}
            className="w-full text-left bg-white border border-muted rounded-[12px] p-4 flex items-center justify-between focus-ring hover:border-graphite transition-colors"
            style={{ boxShadow: '0 2px 8px rgba(69,72,73,0.08)' }}
          >
            <div>
              <p className="text-xs text-subtle font-semibold uppercase tracking-wide mb-1">{label}</p>
              {value ? (
                <div className="flex items-center gap-2">
                  {step === 'time' && localTeam && (
                    <span
                      className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ background: localTeam.accentColor }}
                    />
                  )}
                  <p className="text-[16px] font-semibold text-graphite">{value}</p>
                </div>
              ) : (
                <p className="text-[16px] text-subtle">{placeholder}</p>
              )}
            </div>
            <ChevronIcon />
          </button>
        ))}
      </div>

      {/* CTA */}
      <div className="px-4 max-w-lg mx-auto">
        <button
          onClick={() => navigate('/catalog')}
          disabled={!canContinue}
          className={`w-full py-3.5 rounded-[10px] font-semibold text-[16px] transition-all focus-ring ${
            canContinue
              ? 'bg-graphite text-white hover:bg-graphite/90 active:scale-[0.98]'
              : 'bg-muted text-subtle cursor-not-allowed'
          }`}
        >
          Ver catálogo
        </button>
        <p className="text-center text-xs text-subtle mt-4">
          Não tem conta?{' '}
          <button
            onClick={() => navigate('/signup')}
            className="text-graphite font-semibold underline underline-offset-2 focus-ring rounded"
          >
            Cadastre-se
          </button>
        </p>
      </div>

      {/* Modals */}
      {modal && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
          onClick={() => setModal(null)}
        >
          <div className="absolute inset-0 bg-graphite/40" />
          <div
            className="relative bg-white w-full sm:max-w-md rounded-t-3xl sm:rounded-2xl overflow-hidden"
            style={{ maxHeight: '85vh' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-muted">
              <h2 className="text-[18px] font-semibold italic text-graphite">
                {modal === 'time' ? 'Selecionar time' : modal === 'ano' ? 'Selecionar ano' : 'Selecionar versão'}
              </h2>
              <button
                onClick={() => setModal(null)}
                className="p-1.5 rounded-lg text-subtle hover:bg-surface focus-ring"
              >
                <CloseIcon />
              </button>
            </div>

            {modal === 'time' && (
              <>
                <div className="px-4 py-3 border-b border-muted">
                  <div className="relative">
                    <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-subtle" />
                    <input
                      type="text"
                      placeholder="Buscar time..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 bg-surface rounded-lg text-sm text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite focus:ring-offset-0 border border-transparent focus:border-graphite"
                      autoFocus
                    />
                  </div>
                </div>
                <div className="overflow-y-auto" style={{ maxHeight: 'calc(85vh - 130px)' }}>
                  {filteredTeams.length === 0 && (
                    <p className="text-center text-subtle py-8 text-sm">Nenhum time encontrado</p>
                  )}
                  {filteredTeams.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleSelectTeam(t)}
                      className={`w-full text-left px-5 py-3.5 flex items-center gap-3 hover:bg-surface transition-colors focus-ring ${localTeam?.id === t.id ? 'bg-orange/5' : ''}`}
                    >
                      <span
                        className="w-4 h-4 rounded-full flex-shrink-0 border border-muted"
                        style={{ background: t.accentColor }}
                      />
                      <span className="flex-1 font-semibold text-graphite text-[15px]">{t.name}</span>
                      <span className="text-xs text-subtle font-semibold">{t.state}</span>
                      {localTeam?.id === t.id && <CheckIcon />}
                    </button>
                  ))}
                </div>
              </>
            )}

            {modal === 'ano' && (
              <div className="overflow-y-auto" style={{ maxHeight: 'calc(85vh - 80px)' }}>
                {SEASONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSelectSeason(s)}
                    className={`w-full text-left px-5 py-4 flex items-center justify-between hover:bg-surface focus-ring ${localSeason === s ? 'bg-orange/5' : ''}`}
                  >
                    <span className="font-semibold text-graphite text-[16px]">{s}</span>
                    {localSeason === s && <CheckIcon />}
                  </button>
                ))}
              </div>
            )}

            {modal === 'versao' && (
              <div className="overflow-y-auto" style={{ maxHeight: 'calc(85vh - 80px)' }}>
                {VERSIONS.default.map((v) => (
                  <button
                    key={v}
                    onClick={() => handleSelectVersion(v)}
                    className={`w-full text-left px-5 py-4 flex items-center justify-between hover:bg-surface focus-ring ${localVersion === v ? 'bg-orange/5' : ''}`}
                  >
                    <span className="font-semibold text-graphite text-[16px]">{v}</span>
                    {localVersion === v && <CheckIcon />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ChevronIcon() {
  return (
    <svg className="w-5 h-5 text-subtle flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="w-5 h-5 text-orange flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
