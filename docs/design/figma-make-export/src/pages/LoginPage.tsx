import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';

type View = 'login' | 'forgot';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useApp();

  const [view, setView] = useState<View>('login');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function formatPhone(v: string) {
    const digits = v.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 2) return digits;
    if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  }

  function handleLogin() {
    setError('');
    if (!phone || !password) return;
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      if (password === 'wrongpass') {
        setError('Senha incorreta. Tente novamente.');
        return;
      }
      login('Usuário', phone.replace(/\D/g, ''));
      navigate('/order');
    }, 800);
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="px-4 py-4 flex items-center gap-3 border-b border-muted">
        <button
          onClick={() => view === 'login' ? navigate(-1) : setView('login')}
          className="p-1.5 rounded-lg text-graphite hover:bg-surface focus-ring transition-colors"
        >
          <BackIcon />
        </button>
        <span className="text-[15px] font-semibold text-graphite">
          {view === 'login' ? 'Entrar' : 'Recuperar senha'}
        </span>
      </div>

      <div className="flex-1 px-4 py-8 max-w-sm mx-auto w-full">
        {view === 'login' && (
          <div className="space-y-5">
            <div>
              <h2 className="text-[20px] font-semibold italic text-graphite mb-1">Bem-vindo de volta</h2>
              <p className="text-sm text-subtle">Entre com seu telefone e senha.</p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-subtle uppercase tracking-wide mb-1.5">
                  Telefone (WhatsApp)
                </label>
                <div className="flex gap-2">
                  <div className="flex items-center px-3 py-2.5 bg-surface border border-muted rounded-[10px] text-sm font-semibold text-graphite flex-shrink-0">
                    🇧🇷 +55
                  </div>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(formatPhone(e.target.value))}
                    placeholder="(11) 99999-9999"
                    autoFocus
                    className="flex-1 px-3 py-2.5 bg-surface border border-muted rounded-[10px] text-[15px] text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-subtle uppercase tracking-wide mb-1.5">Senha</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => { setPassword(e.target.value); setError(''); }}
                    onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                    placeholder="Sua senha"
                    className={`w-full px-3 py-2.5 pr-11 bg-surface border rounded-[10px] text-[15px] text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite transition-colors ${error ? 'border-red-400 bg-red-50' : 'border-muted focus:border-graphite'}`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-subtle hover:text-graphite focus-ring rounded transition-colors"
                  >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
                {error && <p className="text-xs text-red-600 font-semibold mt-1">{error}</p>}
              </div>
            </div>

            <button
              onClick={handleLogin}
              disabled={!phone || !password || loading}
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] disabled:opacity-50 hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring flex items-center justify-center gap-2"
            >
              {loading ? <Spinner /> : 'Entrar'}
            </button>

            <button
              onClick={() => setView('forgot')}
              className="w-full text-center text-sm text-subtle hover:text-graphite transition-colors focus-ring rounded py-1"
            >
              Esqueci a senha
            </button>

            <div className="border-t border-muted pt-4 text-center">
              <span className="text-sm text-subtle">Não tem conta? </span>
              <button
                onClick={() => navigate('/signup')}
                className="text-sm font-semibold text-graphite underline underline-offset-2 focus-ring rounded"
              >
                Cadastre-se
              </button>
            </div>
          </div>
        )}

        {view === 'forgot' && (
          <div className="space-y-5">
            <div>
              <h2 className="text-[20px] font-semibold italic text-graphite mb-1">Recuperar senha</h2>
              <p className="text-sm text-subtle leading-relaxed">
                Vamos te levar para a nossa conversa no WhatsApp. Nossa equipe envia um link para criar uma nova senha.
              </p>
            </div>

            <div className="p-4 bg-surface rounded-[12px] border border-muted flex gap-3 items-start">
              <WhatsAppIcon />
              <div>
                <p className="text-[14px] font-semibold text-graphite mb-1">Suporte via WhatsApp</p>
                <p className="text-xs text-subtle leading-relaxed">
                  Ao clicar, você será redirecionado para o WhatsApp da Uniartes Uniformes. Informe seu telefone cadastrado e receba o link de recuperação.
                </p>
              </div>
            </div>

            <a
              href="https://wa.me/5511999999999?text=Preciso%20recuperar%20minha%20senha"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] flex items-center justify-center gap-3 hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring"
            >
              <WhatsAppIcon small />
              Abrir WhatsApp
            </a>

            <button
              onClick={() => setView('login')}
              className="w-full text-center text-sm font-semibold text-subtle hover:text-graphite transition-colors focus-ring rounded py-1"
            >
              Voltar ao login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function WhatsAppIcon({ small }: { small?: boolean }) {
  return (
    <svg
      className={`flex-shrink-0 ${small ? 'w-5 h-5' : 'w-8 h-8'}`}
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"
        fill="#25D366"
      />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
