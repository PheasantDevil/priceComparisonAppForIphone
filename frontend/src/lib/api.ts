export type PriceInfo = {
  official_price: number;
  kaitori_price: number;
  price_diff: number;
  rakuten_diff: number;
};

export type PricesResponse = {
  series: string;
  prices: Record<string, PriceInfo>;
};

export type PriceHistoryData = {
  date: string;
  timestamp: number;
  price_min: number;
  price_max: number;
  price_avg: number;
};

export type PriceHistoryResponse = {
  series: string;
  capacity: string;
  days: number;
  history: PriceHistoryData[];
};

export type ApiStatusResponse = {
  status: string;
  services: {
    api: string;
    database: string;
    storage: string;
  };
  timestamp: string;
};

export type HealthResponse = {
  status: string;
  timestamp: string;
  environment: string;
  version: string;
};

export type OfficialPriceData = {
  id: string;
  series: string;
  capacity: string;
  price: number;
  date: string;
  [key: string]: unknown;
};

// キャッシュの型定義
type CacheEntry = {
  data: PricesResponse;
  timestamp: number;
};

// キャッシュの有効期限（5分）
const CACHE_DURATION = 5 * 60 * 1000;

// メモリキャッシュ
const cache: Record<string, CacheEntry> = {};

// APIのベースURLを取得
const getApiBaseUrl = () => {
  // Vercelの環境変数を使用
  if (typeof window !== 'undefined') {
    // クライアントサイドでは環境変数が利用できないため、相対パスを使用
    return '';
  }
  // サーバーサイドでは環境変数を使用
  return (
    process.env.BACKEND_URL ||
    'https://asia-northeast1-price-comparison-app.cloudfunctions.net'
  );
};

export async function fetchPrices(series: string): Promise<PricesResponse> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/get_prices?series=${encodeURIComponent(series)}`;

  // キャッシュをチェック
  const cached = cache[url];
  const now = Date.now();

  if (cached && now - cached.timestamp < CACHE_DURATION) {
    return cached.data;
  }

  // キャッシュがない、または期限切れの場合は新しいデータを取得
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('API fetch failed');

  const data = await res.json();

  // キャッシュを更新
  cache[url] = {
    data,
    timestamp: now,
  };

  return data;
}

export async function fetchPriceHistory(
  series: string,
  capacity: string,
  days: number = 14
): Promise<PriceHistoryResponse> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/get_price_history?series=${encodeURIComponent(
    series
  )}&capacity=${encodeURIComponent(capacity)}&days=${days}`;

  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Price history API fetch failed');

  return res.json();
}

export async function fetchApiPrices(): Promise<OfficialPriceData[]> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api_prices`;

  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('API prices fetch failed');

  return res.json();
}

export async function fetchApiStatus(): Promise<ApiStatusResponse> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api_status`;

  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('API status fetch failed');

  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/health`;

  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error('Health check failed');

  return res.json();
}

// キャッシュをクリアする関数
export function clearCache() {
  Object.keys(cache).forEach(key => delete cache[key]);
}
