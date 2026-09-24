import { createContext, useContext, useState, ReactNode } from 'react';
import type { Team, Category } from '../data/mockData';

export interface CartItem {
  id: string;
  name: string;
  category: Category;
  widthCm: number;
  heightCm: number;
  quantity: number;
  customName?: string;
}

interface AppState {
  team: Team | null;
  season: string;
  version: string;
  cart: CartItem[];
  isLoggedIn: boolean;
  userName: string;
  userPhone: string;
  notes: string;
}

interface AppContextValue extends AppState {
  setTeam: (team: Team) => void;
  setSeason: (s: string) => void;
  setVersion: (v: string) => void;
  addToCart: (item: Omit<CartItem, 'quantity'>) => void;
  updateQuantity: (id: string, quantity: number) => void;
  removeFromCart: (id: string) => void;
  clearCart: () => void;
  login: (name: string, phone: string) => void;
  logout: () => void;
  setNotes: (n: string) => void;
  cartCount: number;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>({
    team: null,
    season: '2026',
    version: 'Home 1',
    cart: [],
    isLoggedIn: false,
    userName: '',
    userPhone: '',
    notes: '',
  });

  function setTeam(team: Team) {
    setState((s) => ({ ...s, team }));
  }

  function setSeason(season: string) {
    setState((s) => ({ ...s, season }));
  }

  function setVersion(version: string) {
    setState((s) => ({ ...s, version }));
  }

  function addToCart(item: Omit<CartItem, 'quantity'>) {
    setState((s) => {
      const existing = s.cart.find((c) => c.id === item.id);
      if (existing) {
        return {
          ...s,
          cart: s.cart.map((c) => c.id === item.id ? { ...c, quantity: c.quantity + 1 } : c),
        };
      }
      return { ...s, cart: [...s.cart, { ...item, quantity: 1 }] };
    });
  }

  function updateQuantity(id: string, quantity: number) {
    setState((s) => ({
      ...s,
      cart: quantity <= 0
        ? s.cart.filter((c) => c.id !== id)
        : s.cart.map((c) => c.id === id ? { ...c, quantity } : c),
    }));
  }

  function removeFromCart(id: string) {
    setState((s) => ({ ...s, cart: s.cart.filter((c) => c.id !== id) }));
  }

  function clearCart() {
    setState((s) => ({ ...s, cart: [] }));
  }

  function login(name: string, phone: string) {
    setState((s) => ({ ...s, isLoggedIn: true, userName: name, userPhone: phone }));
  }

  function logout() {
    setState((s) => ({ ...s, isLoggedIn: false, userName: '', userPhone: '' }));
  }

  function setNotes(notes: string) {
    setState((s) => ({ ...s, notes }));
  }

  const cartCount = state.cart.reduce((sum, c) => sum + c.quantity, 0);

  return (
    <AppContext.Provider value={{
      ...state,
      setTeam, setSeason, setVersion,
      addToCart, updateQuantity, removeFromCart, clearCart,
      login, logout, setNotes,
      cartCount,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
