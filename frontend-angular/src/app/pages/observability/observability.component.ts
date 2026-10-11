import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { AIRunMetric, ObservabilitySummary } from '../../models/types';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-observability',
  standalone: true,
  imports: [CommonModule, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <app-icon name="activity" class="w-6 h-6 text-blue-400"></app-icon>
          <span>Observability & AI Cost Analytics</span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">
          Track latency, prompt token usage, completion token usage, and estimated LLM expenditure per feature.
        </p>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div class="text-xs text-slate-400 font-medium">Total AI Executions</div>
          <div class="text-2xl font-bold text-slate-100">{{ summary?.total_ai_queries || 0 }}</div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div class="text-xs text-slate-400 font-medium">Total Tokens Consumed</div>
          <div class="text-2xl font-bold text-purple-400">{{ summary?.total_tokens_consumed || 0 }}</div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div class="text-xs text-slate-400 font-medium">Average Latency</div>
          <div class="text-2xl font-bold text-amber-400">{{ summary?.average_latency_ms || 0 }} ms</div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-1">
          <div class="text-xs text-slate-400 font-medium">Estimated LLM Cost</div>
          <div class="text-2xl font-bold text-emerald-400">&#36;{{ summary?.total_cost_usd || '0.0000' }}</div>
        </div>
      </div>

      <!-- Visual Charts Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Latency Trend Chart -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 class="font-bold text-slate-200 text-sm">Query Latency Trend (ms)</h3>
          <div class="h-64 flex flex-col justify-end">
            <div class="flex items-end gap-2 h-48 w-full border-b border-l border-slate-800 px-2 pb-1">
              <div
                *ngFor="let item of chartData; let i = index"
                class="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end"
              >
                <!-- Tooltip -->
                <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 bg-slate-950 border border-slate-800 text-[10px] text-slate-200 px-2 py-0.5 rounded shadow pointer-events-none whitespace-nowrap z-10">
                  {{ item.name }}: {{ item.latency }}ms
                </div>
                <!-- Bar -->
                <div
                  [style.height.%]="getLatencyPercent(item.latency)"
                  class="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t min-h-[4px] transition-all group-hover:brightness-125"
                ></div>
                <span class="text-[10px] text-slate-500 font-mono">{{ item.name }}</span>
              </div>
            </div>
            <div class="flex justify-between text-[11px] text-slate-500 pt-2 font-mono">
              <span>0 ms</span>
              <span>Max: {{ maxLatency }} ms</span>
            </div>
          </div>
        </div>

        <!-- Token Consumption Chart -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h3 class="font-bold text-slate-200 text-sm">Token Consumption per Query</h3>
          <div class="h-64 flex flex-col justify-end">
            <div class="flex items-end gap-2 h-48 w-full border-b border-l border-slate-800 px-2 pb-1">
              <div
                *ngFor="let item of chartData; let i = index"
                class="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end"
              >
                <!-- Tooltip -->
                <div class="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 bg-slate-950 border border-slate-800 text-[10px] text-slate-200 px-2 py-0.5 rounded shadow pointer-events-none whitespace-nowrap z-10">
                  {{ item.name }}: {{ item.tokens }} tokens
                </div>
                <!-- Bar -->
                <div
                  [style.height.%]="getTokenPercent(item.tokens)"
                  class="w-full bg-purple-500 rounded-t min-h-[4px] transition-all group-hover:brightness-125"
                ></div>
                <span class="text-[10px] text-slate-500 font-mono">{{ item.name }}</span>
              </div>
            </div>
            <div class="flex justify-between text-[11px] text-slate-500 pt-2 font-mono">
              <span>0 tokens</span>
              <span>Max: {{ maxTokens }} tokens</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Logs Table -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 class="font-bold text-slate-100 text-base">Execution Logs Table</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs font-mono">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400">
                <th class="py-2.5 px-3">Feature</th>
                <th class="py-2.5 px-3">Model</th>
                <th class="py-2.5 px-3">Prompt Tokens</th>
                <th class="py-2.5 px-3">Completion Tokens</th>
                <th class="py-2.5 px-3">Latency (ms)</th>
                <th class="py-2.5 px-3">Cost ($)</th>
                <th class="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let r of runs" class="border-b border-slate-800/60 hover:bg-slate-800/40">
                <td class="py-2.5 px-3 text-slate-200 font-semibold font-sans">{{ r.feature }}</td>
                <td class="py-2.5 px-3 text-slate-400">{{ r.model }}</td>
                <td class="py-2.5 px-3 text-slate-400">{{ r.prompt_tokens }}</td>
                <td class="py-2.5 px-3 text-slate-400">{{ r.completion_tokens }}</td>
                <td class="py-2.5 px-3 text-amber-400">{{ Math.round(r.latency_ms) }}</td>
                <td class="py-2.5 px-3 text-emerald-400">&#36;{{ formatCost(r.estimated_cost_usd) }}</td>
                <td class="py-2.5 px-3 text-emerald-400">{{ r.status }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class ObservabilityComponent implements OnInit {
  private api = inject(ApiService);

  runs: AIRunMetric[] = [];
  summary: ObservabilitySummary | null = null;
  Math = Math;

  chartData: Array<{ name: string; latency: number; tokens: number; cost: number }> = [];
  maxLatency = 500;
  maxTokens = 2000;

  ngOnInit(): void {
    this.api.getAIRuns().subscribe({
      next: (data) => {
        this.runs = data;
        this.chartData = data.slice(0, 15).reverse().map((r, i) => ({
          name: `Q${i + 1}`,
          latency: Math.round(r.latency_ms),
          tokens: r.prompt_tokens + r.completion_tokens,
          cost: r.estimated_cost_usd
        }));

        if (this.chartData.length > 0) {
          this.maxLatency = Math.max(...this.chartData.map((d) => d.latency), 100);
          this.maxTokens = Math.max(...this.chartData.map((d) => d.tokens), 500);
        }
      },
      error: (err) => console.error(err)
    });

    this.api.getObservabilitySummary().subscribe({
      next: (s) => (this.summary = s),
      error: (err) => console.error(err)
    });
  }

  formatCost(cost: number | undefined): string {
    return (cost !== undefined && cost !== null ? cost : 0).toFixed(6);
  }

  getLatencyPercent(latency: number): number {
    return Math.max(5, Math.min(100, Math.round((latency / this.maxLatency) * 100)));
  }

  getTokenPercent(tokens: number): number {
    return Math.max(5, Math.min(100, Math.round((tokens / this.maxTokens) * 100)));
  }
}
