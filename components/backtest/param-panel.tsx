import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { IndicatorSpec } from "@/lib/types";

interface ParamPanelProps {
  specs: IndicatorSpec[]; // hanya indikator yang terpilih
  params: Record<string, Record<string, number>>;
  onChange: (indicatorKey: string, paramName: string, value: number) => void;
}

export function ParamPanel({ specs, params, onChange }: ParamPanelProps) {
  if (specs.length === 0) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {specs.map((spec) => (
        <div key={spec.key} className="flex flex-col gap-2 rounded-md bg-surface-2 p-3">
          <span className="text-[12.5px] font-medium text-text-primary">{spec.label}</span>
          {Object.entries(spec.params).map(([pname, pcfg]) => (
            <div key={pname} className="flex flex-col gap-1">
              <Label htmlFor={`${spec.key}-${pname}`} className="text-[11px] text-text-muted">
                {pname}
              </Label>
              <Input
                id={`${spec.key}-${pname}`}
                type="number"
                value={params[spec.key]?.[pname] ?? pcfg.default}
                min={pcfg.min ?? undefined}
                max={pcfg.max ?? undefined}
                step={pcfg.type === "float" ? 0.1 : 1}
                onChange={(e) => onChange(spec.key, pname, Number(e.target.value))}
                className="h-7 px-2 text-[12px]"
              />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
