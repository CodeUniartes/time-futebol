import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';
import { MOCK_ORDERS, STATUS_LABELS, STATUS_COLORS } from '../data/mockData';

type Tab = 'pedidos' | 'artes';

export default function MyOrdersPage() {
  const navigate = useNavigate();
  const { isLoggedIn } = useApp();
  const [tab, setTab] = useState<Tab>('pedidos');

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16 text-center">
        <div className="w-20 h-20 rounded-full bg-surface flex items-center justify-center mb-4">
          <LockIcon />
        </div>
        <h2 className="text-xl font-semibold italic text-graphite mb-2">Área protegida</h2>
        <p className="text-subtle text-sm mb-6">Entre na sua conta para ver seus pedidos.</p>
        <button
          onClick={() => navigate('/login')}
          className="bg-graphite text-white px-6 py-3 rounded-[10px] font-semibold text-[15px] hover:bg-graphite/90 transition-colors focus-ring"
        >
          Entrar
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-screen-md mx-auto px-4 py-4">
      <h1 className="text-[22px] font-semibold italic text-graphite mb-4">Minha conta</h1>

      {/* Tabs */}
      <div className="flex border-b border-muted mb-4">
        {(['pedidos', 'artes'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-[14px] font-semibold transition-colors border-b-2 capitalize focus-ring ${
              tab === t ? 'border-orange text-graphite' : 'border-transparent text-subtle hover:text-graphite'
            }`}
          >
            {t === 'pedidos' ? 'Meus pedidos' : 'Minhas artes'}
          </button>
        ))}
      </div>

      {tab === 'pedidos' && (
        <div>
          {MOCK_ORDERS.length === 0 ? (
            <EmptyState
              icon={<BoxIcon />}
              title="Nenhum pedido ainda"
              description="Seus pedidos DTF aparecerão aqui."
              action={{ label: 'Fazer meu primeiro pedido', onClick: () => navigate('/') }}
            />
          ) : (
            <div className="space-y-3">
              {MOCK_ORDERS.map((order) => (
                <div
                  key={order.id}
                  className="bg-white border border-muted rounded-[12px] p-4"
                  style={{ boxShadow: '0 2px 8px rgba(69,72,73,0.06)' }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <span
                        className="text-lg font-semibold tracking-[0.12em] text-graphite"
                        style={{ fontVariantNumeric: 'tabular-nums' }}
                      >
                        {order.code}
                      </span>
                      <p className="text-xs text-subtle mt-0.5">{order.team} · {order.date}</p>
                    </div>
                    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${STATUS_COLORS[order.status]}`}>
                      {STATUS_LABELS[order.status]}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-subtle">
                      {order.totalPieces} peça{order.totalPieces !== 1 ? 's' : ''}
                    </span>
                    <button
                      onClick={() => navigate('/')}
                      className="text-sm font-semibold text-graphite border border-muted px-3 py-1.5 rounded-[8px] hover:bg-surface transition-colors focus-ring flex items-center gap-1"
                    >
                      <RefreshIcon />
                      Refazer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'artes' && (
        <EmptyState
          icon={<ImageIcon />}
          title="Nenhuma arte salva"
          description="Suas artes personalizadas enviadas aparecerão aqui."
          action={{ label: 'Enviar minha arte', onClick: () => navigate('/add-art') }}
        />
      )}
    </div>
  );
}

function EmptyState({ icon, title, description, action }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action: { label: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-center text-center py-16">
      <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mb-4 text-muted">{icon}</div>
      <h3 className="text-[16px] font-semibold text-graphite mb-1">{title}</h3>
      <p className="text-sm text-subtle mb-6">{description}</p>
      <button
        onClick={action.onClick}
        className="bg-graphite text-white px-5 py-2.5 rounded-[10px] text-sm font-semibold hover:bg-graphite/90 transition-colors focus-ring"
      >
        {action.label}
      </button>
    </div>
  );
}

function LockIcon() {
  return <svg className="w-9 h-9 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>;
}

function BoxIcon() {
  return <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></svg>;
}

function ImageIcon() {
  return <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>;
}

function RefreshIcon() {
  return <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 .49-4.5" /></svg>;
}
