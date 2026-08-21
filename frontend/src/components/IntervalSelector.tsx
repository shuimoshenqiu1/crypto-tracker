import { Segmented } from 'antd';

const INTERVALS = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1d', value: '1d' },
];

interface IntervalSelectorProps {
  value: string;
  onChange: (interval: string) => void;
}

export default function IntervalSelector({ value, onChange }: IntervalSelectorProps) {
  return (
    <Segmented
      options={INTERVALS}
      value={value}
      onChange={(val) => onChange(val as string)}
    />
  );
}
