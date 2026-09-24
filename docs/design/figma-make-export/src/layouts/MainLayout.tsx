import { Outlet, useLocation, useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';

const TABS = [
  { path: '/catalog', label: 'Catálogo', icon: GridIcon },
  { path: '/order', label: 'Pedido', icon: CartIcon, badge: true },
  { path: '/add-art', label: 'Minhas Artes', icon: ImageIcon },
  { path: '/my-orders', label: 'Meus Pedidos', icon: ListIcon },
];

const NO_TAB_PATHS = ['/', '/signup', '/login', '/order-sent'];
const NO_HEADER_PATHS = ['/signup', '/login', '/order-sent'];

export default function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { cartCount, isLoggedIn, userName, logout } = useApp();

  const showTabs = !NO_TAB_PATHS.includes(location.pathname);
  const showHeader = !NO_HEADER_PATHS.includes(location.pathname);
  const isStart = location.pathname === '/';

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {showHeader && (
        <header className="sticky top-0 z-40 bg-white border-b border-muted" style={{ boxShadow: '0 1px 4px rgba(69,72,73,0.08)' }}>
          <div className="max-w-screen-xl mx-auto px-4 flex items-center justify-between h-14">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 focus-ring rounded-lg"
              aria-label="Início"
            >
              <div
                className="flex items-center justify-center rounded-xl bg-surface border border-muted"
                style={{ width: 38, height: 38 }}
              >
                <span className="text-[9px] font-semibold text-subtle leading-tight text-center px-1">Logo<br />Uniartes</span>
              </div>
              {!isStart && (
                <span className="text-sm font-semibold text-graphite tracking-wide hidden sm:block">Pedido DTF</span>
              )}
            </button>

            <div className="flex items-center gap-2">
              {isLoggedIn ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-subtle hidden sm:block">{userName}</span>
                  <button
                    onClick={logout}
                    className="text-sm font-semibold text-graphite focus-ring rounded-lg px-3 py-1.5 hover:bg-surface transition-colors"
                  >
                    Sair
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => navigate('/login')}
                  className="text-sm font-semibold text-graphite focus-ring rounded-lg px-3 py-1.5 hover:bg-surface transition-colors"
                >
                  Entrar
                </button>
              )}
            </div>
          </div>
        </header>
      )}

      <main className={`flex-1 ${showTabs ? 'pb-20' : ''}`}>
        <Outlet />
      </main>

      {showTabs && (
        <nav
          className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-muted"
          style={{ boxShadow: '0 -2px 8px rgba(69,72,73,0.08)' }}
          aria-label="Navegação principal"
        >
          <div className="max-w-screen-xl mx-auto flex">
            {TABS.map(({ path, label, icon: Icon, badge }) => {
              const active = location.pathname === path;
              return (
                <button
                  key={path}
                  onClick={() => navigate(path)}
                  className={`flex-1 flex flex-col items-center gap-0.5 py-2 px-1 focus-ring transition-colors min-h-[44px] ${active ? 'text-graphite' : 'text-subtle hover:text-graphite'}`}
                  aria-current={active ? 'page' : undefined}
                >
                  <div className="relative">
                    <Icon className={`w-5 h-5 ${active ? 'text-graphite' : ''}`} />
                    {badge && cartCount > 0 && (
                      <span className="absolute -top-1.5 -right-2 bg-orange text-white text-[10px] font-semibold rounded-full min-w-[16px] h-4 flex items-center justify-center px-1 leading-none">
                        {cartCount > 99 ? '99+' : cartCount}
                      </span>
                    )}
                  </div>
                  <span className={`text-[10px] font-semibold leading-none ${active ? 'text-graphite' : ''}`}>{label}</span>
                  {active && <div className="absolute top-0 w-8 h-0.5 bg-orange rounded-full" />}
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}

function GridIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}

function CartIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <path d="M16 10a4 4 0 0 1-8 0" />
    </svg>
  );
}

function ImageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  );
}

function ListIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  );
}
