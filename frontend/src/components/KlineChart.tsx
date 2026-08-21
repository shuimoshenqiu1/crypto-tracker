import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData, HistogramData, Time } from 'lightweight-charts';
import { Spin, Empty } from 'antd';
import { getKlines } from '../services/klines';

interface KlineChartProps {
  coinId: string;
  interval: string;
}

function getTimeRange(interval: string): { start_time: number; end_time: number } {
  const now = Date.now();
  let ms: number;
  switch (interval) {
    case '1m':
    case '5m':
    case '15m':
      ms = 24 * 60 * 60 * 1000; // 24h
      break;
    case '4h':
    case '1d':
      ms = 30 * 24 * 60 * 60 * 1000; // 30 days
      break;
    case '1h':
    default:
      ms = 7 * 24 * 60 * 60 * 1000; // 7 days
      break;
  }
  return { start_time: now - ms, end_time: now };
}

export default function KlineChart({ coinId, interval }: KlineChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const [loading, setLoading] = useState(true);
  const [empty, setEmpty] = useState(false);

  // Create chart on mount
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 0,
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderDownColor: '#ef5350',
      borderUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      wickUpColor: '#26a69a',
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // Fetch data when coinId or interval changes
  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setEmpty(false);
      try {
        const { start_time, end_time } = getTimeRange(interval);
        const res = await getKlines(coinId, { interval, start_time, end_time, limit: 1500 });
        if (cancelled) return;

        const klines = res.data.klines;
        if (!klines || klines.length === 0) {
          setEmpty(true);
          candlestickSeriesRef.current?.setData([]);
          volumeSeriesRef.current?.setData([]);
          return;
        }

        const candleData: CandlestickData<Time>[] = klines.map((k) => ({
          time: (k.open_time / 1000) as Time,
          open: k.open,
          high: k.high,
          low: k.low,
          close: k.close,
        }));

        const volumeData: HistogramData<Time>[] = klines.map((k) => ({
          time: (k.open_time / 1000) as Time,
          value: k.volume,
          color: k.close >= k.open ? 'rgba(38,166,154,0.5)' : 'rgba(239,83,80,0.5)',
        }));

        candlestickSeriesRef.current?.setData(candleData);
        volumeSeriesRef.current?.setData(volumeData);
        chartRef.current?.timeScale().fitContent();
      } catch {
        // silently handle fetch errors; user sees empty chart
        if (!cancelled) setEmpty(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, [coinId, interval]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {loading && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(255,255,255,0.7)', zIndex: 10,
        }}>
          <Spin size="large" />
        </div>
      )}
      {empty && !loading && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 10,
        }}>
          <Empty description="No data" />
        </div>
      )}
      <div ref={chartContainerRef} style={{ width: '100%', height: 400 }} />
    </div>
  );
}
