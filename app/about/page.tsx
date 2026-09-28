import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ArchitectureTab } from "@/components/about/architecture-tab";
import { SignalEngineTab } from "@/components/about/signal-engine-tab";
import { RiskManagementTab } from "@/components/about/risk-management-tab";
import { LimitationsGlossaryTab } from "@/components/about/limitations-glossary-tab";
import {
  Cpu,
  Activity,
  ShieldCheck,
  BookOpen,
  Layers,
  Scale,
  Sparkles,
} from "lucide-react";

export default function AboutPage() {
  return (
    <div className="flex flex-col gap-5">
      {/* Top Header Section */}
      <div className="flex flex-col gap-3">
        <PageHeader
          title="Metodologi & Parameter Kuantitatif"
          description="Transparansi Algoritma, Manajemen Risiko Portofolio, dan Validasi Empiris IDX30/LQ45"
          className="mb-1"
          action={
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <Badge variant="outline" className="border-border bg-surface-1 text-text-secondary text-[11px]">
                <Layers className="size-3 text-blue-400" /> Universe: LQ45 &amp; IDX30
              </Badge>
              <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px]">
                <ShieldCheck className="size-3" /> Hybrid 2-Tier Exit
              </Badge>
              <Badge variant="outline" className="border-purple-500/30 bg-purple-500/10 text-purple-400 text-[11px]">
                <Sparkles className="size-3" /> TradingView Bar Replay
              </Badge>
              <Badge variant="outline" className="border-border bg-surface-1 text-text-secondary text-[11px]">
                <Scale className="size-3 text-amber-400" /> Max 7 Slots
              </Badge>
            </div>
          }
        />
      </div>

      {/* Tabbed Bento Layout */}
      <Tabs defaultValue="architecture" className="w-full">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 h-auto p-1 bg-surface-1 border border-border">
          <TabsTrigger value="architecture" className="flex items-center gap-1.5 py-2 text-xs">
            <Cpu className="size-3.5 text-blue-400" />
            <span>Pipeline &amp; Data</span>
          </TabsTrigger>
          <TabsTrigger value="signals" className="flex items-center gap-1.5 py-2 text-xs">
            <Activity className="size-3.5 text-emerald-400" />
            <span>Engine Sinyal</span>
          </TabsTrigger>
          <TabsTrigger value="risk" className="flex items-center gap-1.5 py-2 text-xs">
            <ShieldCheck className="size-3.5 text-purple-400" />
            <span>Manajemen Risiko</span>
          </TabsTrigger>
          <TabsTrigger value="glossary" className="flex items-center gap-1.5 py-2 text-xs">
            <BookOpen className="size-3.5 text-amber-400" />
            <span>Kamus &amp; Batasan</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="architecture" className="mt-3">
          <ArchitectureTab />
        </TabsContent>

        <TabsContent value="signals" className="mt-3">
          <SignalEngineTab />
        </TabsContent>

        <TabsContent value="risk" className="mt-3">
          <RiskManagementTab />
        </TabsContent>

        <TabsContent value="glossary" className="mt-3">
          <LimitationsGlossaryTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
