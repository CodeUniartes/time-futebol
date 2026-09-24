export interface Team {
  id: string;
  name: string;
  state: string;
  accentColor: string;
}

export const TEAMS: Team[] = [
  { id: 'atm', name: 'Atlético Mineiro', state: 'MG', accentColor: '#1a1a1a' },
  { id: 'fla', name: 'Flamengo', state: 'RJ', accentColor: '#d40000' },
  { id: 'pal', name: 'Palmeiras', state: 'SP', accentColor: '#006437' },
  { id: 'san', name: 'Santos', state: 'SP', accentColor: '#000000' },
  { id: 'sao', name: 'São Paulo', state: 'SP', accentColor: '#cc0000' },
  { id: 'cor', name: 'Corinthians', state: 'SP', accentColor: '#1a1a1a' },
  { id: 'int', name: 'Internacional', state: 'RS', accentColor: '#c8102e' },
  { id: 'gre', name: 'Grêmio', state: 'RS', accentColor: '#005ca9' },
  { id: 'bot', name: 'Botafogo', state: 'RJ', accentColor: '#000000' },
  { id: 'flu', name: 'Fluminense', state: 'RJ', accentColor: '#6d1f3e' },
  { id: 'bah', name: 'Bahia', state: 'BA', accentColor: '#005baa' },
  { id: 'ath', name: 'Athletico-PR', state: 'PR', accentColor: '#cc0000' },
  { id: 'fga', name: 'Fortaleza', state: 'CE', accentColor: '#004a8f' },
  { id: 'cru', name: 'Cruzeiro', state: 'MG', accentColor: '#003087' },
  { id: 'ame', name: 'América Mineiro', state: 'MG', accentColor: '#008000' },
  { id: 'vas', name: 'Vasco', state: 'RJ', accentColor: '#000000' },
];

export const SEASONS = ['2026', '2025', '2024', '2023'];

export const VERSIONS: Record<string, string[]> = {
  default: ['Home 1', 'Home 2', 'Away 1', 'Away 2', 'Third 1', 'Goleiro'],
};

export type Category = 'letras' | 'fila' | 'costas' | 'frente' | 'logos' | 'camisa';

export interface CatalogItem {
  id: string;
  name: string;
  category: Category;
  widthCm: number;
  heightCm: number;
  previewChar?: string;
  color?: string;
}

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

export const CATALOG_ITEMS: CatalogItem[] = [
  ...LETTERS.map((l) => ({
    id: `letra-${l}`,
    name: `Letra ${l}`,
    category: 'letras' as Category,
    widthCm: 5.4,
    heightCm: 8,
    previewChar: l,
  })),
  { id: 'fila-1', name: 'Fila Completa (até 10 letras)', category: 'fila', widthCm: 25, heightCm: 8 },
  { id: 'fila-2', name: 'Fila Grande (até 14 letras)', category: 'fila', widthCm: 35, heightCm: 8 },
  { id: 'num-costas-1', name: 'Número Costas — Estilo 1', category: 'costas', widthCm: 25, heightCm: 20 },
  { id: 'num-costas-2', name: 'Número Costas — Estilo 2', category: 'costas', widthCm: 25, heightCm: 20 },
  { id: 'num-costas-3', name: 'Número Costas — Estilo 3', category: 'costas', widthCm: 22, heightCm: 18 },
  { id: 'num-frente-1', name: 'Número Frente — Estilo 1', category: 'frente', widthCm: 10, heightCm: 8 },
  { id: 'num-frente-2', name: 'Número Frente — Estilo 2', category: 'frente', widthCm: 10, heightCm: 8 },
  { id: 'logo-1', name: 'Logo Patrocinador P', category: 'logos', widthCm: 8, heightCm: 5 },
  { id: 'logo-2', name: 'Logo Patrocinador M', category: 'logos', widthCm: 14, heightCm: 8 },
  { id: 'logo-3', name: 'Logo Patrocinador G', category: 'logos', widthCm: 20, heightCm: 10 },
  { id: 'camisa-1', name: 'Arte Camisa Completa', category: 'camisa', widthCm: 48, heightCm: 58 },
  { id: 'camisa-2', name: 'Arte Camisa Frente', category: 'camisa', widthCm: 35, heightCm: 45 },
  { id: 'camisa-3', name: 'Arte Camisa Costas', category: 'camisa', widthCm: 35, heightCm: 45 },
];

export const CATEGORY_LABELS: Record<Category, string> = {
  letras: 'Letras',
  fila: 'Fila completa',
  costas: 'Número costas',
  frente: 'Número frente',
  logos: 'Logos',
  camisa: 'Camisa completa',
};

export interface MockOrder {
  id: string;
  code: string;
  date: string;
  status: 'pendente' | 'em_producao' | 'concluido' | 'enviado';
  totalPieces: number;
  team: string;
}

export const MOCK_ORDERS: MockOrder[] = [
  { id: '1', code: 'DTF-7K3F', date: '22/09/2026', status: 'em_producao', totalPieces: 34, team: 'Atlético Mineiro' },
  { id: '2', code: 'DTF-2R9X', date: '15/09/2026', status: 'concluido', totalPieces: 18, team: 'Flamengo' },
  { id: '3', code: 'DTF-4M1Z', date: '08/09/2026', status: 'enviado', totalPieces: 52, team: 'Palmeiras' },
];

export const STATUS_LABELS: Record<MockOrder['status'], string> = {
  pendente: 'Pendente',
  em_producao: 'Em produção',
  concluido: 'Concluído',
  enviado: 'Enviado',
};

export const STATUS_COLORS: Record<MockOrder['status'], string> = {
  pendente: 'bg-yellow-100 text-yellow-800',
  em_producao: 'bg-orange/10 text-dark-orange',
  concluido: 'bg-green-100 text-green-800',
  enviado: 'bg-blue-100 text-blue-800',
};
