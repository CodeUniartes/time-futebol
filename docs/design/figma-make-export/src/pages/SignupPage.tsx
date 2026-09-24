import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';

type Step = 1 | 2 | 3 | 4;

export default function SignupPage() {
  const navigate = useNavigate();
  const { login } = useApp();

  const [step, setStep] = useState<Step>(1);
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [timer, setTimer] = useState(60);
  const [timerActive, setTimerActive] = useState(false);
  const [codeError, setCodeError] = useState('');
  const [loading, setLoading] = useState(false);

  const codeRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (!timerActive) return;
    if (timer <= 0) { setTimerActive(false); return; }
    const t = setTimeout(() => setTimer((n) => n - 1), 1000);
    return () => clearTimeout(t);
  }, [timer, timerActive]);

  function formatPhone(v: string) {
    const digits = v.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 2) return digits;
    if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  }

  function handleStep1() {
    if (!phone || !name) return;
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setStep(2);
      setTimer(60);
      setTimerActive(true);
      setTimeout(() => codeRefs.current[0]?.focus(), 100);
    }, 800);
  }

  function handleCodeInput(i: number, v: string) {
    const char = v.replace(/\D/g, '').slice(-1);
    const newCode = [...code];
    newCode[i] = char;
    setCode(newCode);
    setCodeError('');
    if (char && i < 5) {
      codeRefs.current[i + 1]?.focus();
    }
  }

  function handleCodeKeyDown(i: number, e: React.KeyboardEvent) {
    if (e.key === 'Backspace' && !code[i] && i > 0) {
      codeRefs.current[i - 1]?.focus();
    }
  }

  function handleStep2() {
    const full = code.join('');
    if (full.length < 6) { setCodeError('Digite o código completo.'); return; }
    if (full !== '123456') { setCodeError('Código incorreto. Tente novamente.'); return; }
    setStep(3);
  }

  function getStrength(pw: string) {
    if (pw.length < 4) return 0;
    if (pw.length < 6) return 1;
    if (pw.length < 8) return 2;
    if (/[A-Z]/.test(pw) && /[0-9]/.test(pw)) return 4;
    return 3;
  }

  function handleStep3() {
    if (password.length < 8) return;
    setLoading(true);
    const rawPhone = phone.replace(/\D/g, '');
    setTimeout(() => {
      setLoading(false);
      login(name, rawPhone);
      setStep(4);
    }, 600);
  }

  const strengthLabels = ['', 'Fraca', 'Média', 'Boa', 'Forte'];
  const strengthColors = ['', 'bg-red-400', 'bg-yellow-400', 'bg-green-400', 'bg-green-600'];
  const strength = getStrength(password);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Back header */}
      <div className="px-4 py-4 flex items-center gap-3 border-b border-muted">
        <button
          onClick={() => step === 1 ? navigate(-1) : setStep((s) => (s - 1) as Step)}
          className="p-1.5 rounded-lg text-graphite hover:bg-surface focus-ring transition-colors"
        >
          <BackIcon />
        </button>
        <span className="text-[15px] font-semibold text-graphite">
          {step === 4 ? 'Conta criada!' : 'Criar conta'}
        </span>
      </div>

      {/* Progress steps */}
      {step < 4 && (
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-center gap-2 max-w-sm mx-auto">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center flex-1 gap-2">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 ${
                  step > s ? 'bg-graphite text-white' : step === s ? 'bg-orange text-white' : 'bg-muted text-subtle'
                }`}>
                  {step > s ? <CheckSmall /> : s}
                </div>
                {s < 3 && <div className={`h-0.5 flex-1 rounded-full ${step > s ? 'bg-graphite' : 'bg-muted'}`} />}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-1 max-w-sm mx-auto">
            {['Dados', 'Código', 'Senha'].map((l) => (
              <span key={l} className="text-[10px] text-subtle font-semibold">{l}</span>
            ))}
          </div>
        </div>
      )}

      <div className="flex-1 px-4 py-6 max-w-sm mx-auto w-full">
        {/* Step 1 */}
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-[20px] font-semibold italic text-graphite mb-1">Seus dados</h2>
              <p className="text-sm text-subtle">Vamos te identificar no WhatsApp para envio do código.</p>
            </div>
            <div className="space-y-3">
              <LabeledInput
                label="Seu nome"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Carlos Rodrigues"
                autoFocus
              />
              <div>
                <label className="block text-xs font-semibold text-subtle uppercase tracking-wide mb-1.5">
                  Telefone (WhatsApp) <span className="text-orange">*</span>
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
                    className="flex-1 px-3 py-2.5 bg-surface border border-muted rounded-[10px] text-[15px] text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
                  />
                </div>
              </div>
            </div>
            <button
              onClick={handleStep1}
              disabled={!phone || !name || loading}
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] disabled:opacity-50 hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring flex items-center justify-center gap-2"
            >
              {loading ? <Spinner /> : 'Enviar código'}
            </button>
          </div>
        )}

        {/* Step 2 */}
        {step === 2 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-[20px] font-semibold italic text-graphite mb-1">Código de verificação</h2>
              <p className="text-sm text-subtle">
                Enviamos um código para o seu WhatsApp{' '}
                <span className="font-semibold text-graphite">{phone}</span>.
              </p>
            </div>
            <div className="flex gap-2 justify-center">
              {code.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => { codeRefs.current[i] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleCodeInput(i, e.target.value)}
                  onKeyDown={(e) => handleCodeKeyDown(i, e)}
                  onFocus={(e) => e.target.select()}
                  className={`w-12 h-14 text-center text-xl font-semibold text-graphite bg-surface rounded-[10px] border-2 focus:outline-none transition-colors ${
                    codeError
                      ? 'border-red-400 bg-red-50'
                      : digit
                      ? 'border-graphite'
                      : 'border-muted focus:border-graphite'
                  }`}
                  style={{ fontVariantNumeric: 'tabular-nums' }}
                />
              ))}
            </div>
            {codeError && (
              <p className="text-center text-sm text-red-600 font-semibold">{codeError}</p>
            )}
            <p className="text-center text-sm text-subtle">
              {timerActive ? (
                <>Reenviar código em <span className="font-semibold text-graphite">{timer}s</span></>
              ) : (
                <button
                  onClick={() => { setTimer(60); setTimerActive(true); setCode(['', '', '', '', '', '']); setCodeError(''); }}
                  className="text-graphite font-semibold underline underline-offset-2 focus-ring rounded"
                >
                  Reenviar código
                </button>
              )}
            </p>
            <p className="text-center text-xs text-subtle">Dica: use o código <strong>123456</strong> para testar</p>
            <button
              onClick={handleStep2}
              disabled={code.join('').length < 6}
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] disabled:opacity-50 hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring"
            >
              Verificar
            </button>
          </div>
        )}

        {/* Step 3 */}
        {step === 3 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-[20px] font-semibold italic text-graphite mb-1">Criar senha</h2>
              <p className="text-sm text-subtle">Mínimo de 8 caracteres.</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-subtle uppercase tracking-wide mb-1.5">
                Senha <span className="text-orange">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Digite sua senha"
                  autoFocus
                  className="w-full px-3 py-2.5 pr-11 bg-surface border border-muted rounded-[10px] text-[15px] text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-subtle hover:text-graphite focus-ring rounded transition-colors"
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
              {password.length > 0 && (
                <div className="mt-2">
                  <div className="flex gap-1 mb-1">
                    {[1, 2, 3, 4].map((s) => (
                      <div
                        key={s}
                        className={`h-1 flex-1 rounded-full transition-colors ${strength >= s ? strengthColors[strength] : 'bg-muted'}`}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-subtle">
                    Força: <span className="font-semibold text-graphite">{strengthLabels[strength]}</span>
                  </p>
                </div>
              )}
            </div>
            <button
              onClick={handleStep3}
              disabled={password.length < 8 || loading}
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] disabled:opacity-50 hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring flex items-center justify-center gap-2"
            >
              {loading ? <Spinner /> : 'Criar conta'}
            </button>
          </div>
        )}

        {/* Step 4 – Success */}
        {step === 4 && (
          <div className="flex flex-col items-center text-center py-8">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mb-5">
              <svg className="w-10 h-10 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h2 className="text-[22px] font-semibold italic text-graphite mb-2">Conta criada!</h2>
            <p className="text-sm text-subtle mb-8">
              Bem-vindo, <span className="font-semibold text-graphite">{name}</span>! Agora você pode finalizar seu pedido.
            </p>
            <button
              onClick={() => navigate('/order')}
              className="w-full bg-graphite text-white py-3.5 rounded-[10px] font-semibold text-[16px] hover:bg-graphite/90 transition-all active:scale-[0.98] focus-ring"
            >
              Voltar ao pedido
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function LabeledInput({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div>
      <label className="block text-xs font-semibold text-subtle uppercase tracking-wide mb-1.5">{label}</label>
      <input
        {...props}
        className="w-full px-3 py-2.5 bg-surface border border-muted rounded-[10px] text-[15px] text-graphite placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-graphite focus:border-graphite transition-colors"
      />
    </div>
  );
}

function BackIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function CheckSmall() {
  return (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg className="w-4.5 h-4.5 w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
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
