import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IconComponent } from '../../components/common/icon/icon.component';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <div class="p-8 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 class="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
          <app-icon name="settings" class="w-6 h-6 text-slate-400"></app-icon>
          <span>Platform Settings</span>
        </h1>
        <p class="text-sm text-slate-400 mt-1">Configure LLM providers, vector indexing parameters, and security limits.</p>
      </div>

      <form (ngSubmit)="handleSave()" class="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-6 shadow-sm">
        <div class="space-y-4">
          <h3 class="font-bold text-slate-200 text-sm flex items-center gap-2 border-b border-slate-800 pb-2">
            <app-icon name="key" class="w-4 h-4 text-blue-400"></app-icon>
            <span>LLM Provider Settings</span>
          </h3>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Provider Mode</label>
            <select
              [(ngModel)]="provider"
              name="provider"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-blue-500 cursor-pointer"
            >
              <option value="azure">Azure OpenAI</option>
              <option value="openai">Standard OpenAI</option>
              <option value="mock">Local Development Mock</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">Azure Endpoint</label>
            <input
              type="text"
              [(ngModel)]="endpoint"
              name="endpoint"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1">API Key</label>
            <input
              type="password"
              [(ngModel)]="apiKey"
              name="apiKey"
              class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">LLM Deployment Name</label>
              <input
                type="text"
                [(ngModel)]="deployment"
                name="deployment"
                class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Embedding Deployment</label>
              <input
                type="text"
                [(ngModel)]="embeddingDeployment"
                name="embeddingDeployment"
                class="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          class="bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-2.5 rounded-lg text-sm transition-all shadow-md shadow-blue-600/20 flex items-center gap-2"
        >
          <app-icon [name]="saved ? 'check' : 'save'" class="w-4 h-4"></app-icon>
          <span>{{ saved ? 'Settings Saved!' : 'Save Settings' }}</span>
        </button>
      </form>
    </div>
  `
})
export class SettingsComponent {
  provider = 'azure';
  endpoint = 'https://my-azure-openai.openai.azure.com/';
  apiKey = '••••••••••••••••••••••••';
  deployment = 'gpt-4o';
  embeddingDeployment = 'text-embedding-3-small';
  saved = false;

  handleSave(): void {
    this.saved = true;
    setTimeout(() => {
      this.saved = false;
    }, 2000);
  }
}
