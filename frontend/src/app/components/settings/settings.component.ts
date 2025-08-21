import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { SliderModule } from 'primeng/slider';
import { ToggleButtonModule } from 'primeng/togglebutton';
import { TabViewModule } from 'primeng/tabview';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { DividerModule } from 'primeng/divider';
import { MessageService, ConfirmationService } from 'primeng/api';
import { trigger, state, style, transition, animate } from '@angular/animations';

interface APIConfiguration {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  enableDebugLogging: boolean;
}

interface GenerationSettings {
  defaultOutputFormat: string;
  includeBusinessRules: boolean;
  includeDiagrams: boolean;
  includeArchitecture: boolean;
  maxFileSize: number;
  excludePatterns: string[];
  templateStyle: string;
}

interface SystemPreferences {
  theme: string;
  language: string;
  timezone: string;
  autoRefresh: boolean;
  refreshInterval: number;
  enableNotifications: boolean;
  notificationSound: boolean;
}

interface CacheSettings {
  enableCaching: boolean;
  cacheExpiration: number;
  maxCacheSize: number;
  autoClearCache: boolean;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    InputNumberModule,
    DropdownModule,
    CheckboxModule,
    SliderModule,
    ToggleButtonModule,
    TabViewModule,
    ToastModule,
    ConfirmDialogModule,
    TooltipModule,
    DividerModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
  animations: [
    trigger('slideIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class SettingsComponent implements OnInit {
  loading: boolean = false;
  unsavedChanges: boolean = false;

  // Settings objects
  apiConfig: APIConfiguration = {
    baseUrl: 'http://localhost:8001',
    timeout: 30000,
    retryAttempts: 3,
    enableDebugLogging: false
  };

  generationSettings: GenerationSettings = {
    defaultOutputFormat: 'markdown',
    includeBusinessRules: true,
    includeDiagrams: true,
    includeArchitecture: true,
    maxFileSize: 10,
    excludePatterns: ['*.log', '*.tmp', 'node_modules/*', '.git/*'],
    templateStyle: 'professional'
  };

  systemPreferences: SystemPreferences = {
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
    autoRefresh: true,
    refreshInterval: 30,
    enableNotifications: true,
    notificationSound: false
  };

  cacheSettings: CacheSettings = {
    enableCaching: true,
    cacheExpiration: 3600,
    maxCacheSize: 500,
    autoClearCache: true
  };

  // Dropdown options
  outputFormatOptions = [
    { label: 'Markdown', value: 'markdown' },
    { label: 'HTML', value: 'html' },
    { label: 'PDF', value: 'pdf' },
    { label: 'Word Document', value: 'docx' }
  ];

  templateStyleOptions = [
    { label: 'Professional', value: 'professional' },
    { label: 'Technical', value: 'technical' },
    { label: 'Minimal', value: 'minimal' },
    { label: 'Detailed', value: 'detailed' }
  ];

  themeOptions = [
    { label: 'Light', value: 'light' },
    { label: 'Dark', value: 'dark' },
    { label: 'Auto', value: 'auto' }
  ];

  languageOptions = [
    { label: 'English', value: 'en' },
    { label: 'Spanish', value: 'es' },
    { label: 'French', value: 'fr' },
    { label: 'German', value: 'de' }
  ];

  timezoneOptions = [
    { label: 'UTC', value: 'UTC' },
    { label: 'Eastern Time', value: 'America/New_York' },
    { label: 'Central Time', value: 'America/Chicago' },
    { label: 'Mountain Time', value: 'America/Denver' },
    { label: 'Pacific Time', value: 'America/Los_Angeles' },
    { label: 'European Central', value: 'Europe/Berlin' },
    { label: 'Tokyo', value: 'Asia/Tokyo' }
  ];

  // Original settings for reset functionality
  private originalSettings: any;

  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadSettings();
    this.saveOriginalSettings();
  }

  private loadSettings() {
    this.loading = true;
    
    // Load settings from localStorage or API
    try {
      const savedApiConfig = localStorage.getItem('docxp_api_config');
      if (savedApiConfig) {
        this.apiConfig = { ...this.apiConfig, ...JSON.parse(savedApiConfig) };
      }

      const savedGenerationSettings = localStorage.getItem('docxp_generation_settings');
      if (savedGenerationSettings) {
        this.generationSettings = { ...this.generationSettings, ...JSON.parse(savedGenerationSettings) };
      }

      const savedSystemPreferences = localStorage.getItem('docxp_system_preferences');
      if (savedSystemPreferences) {
        this.systemPreferences = { ...this.systemPreferences, ...JSON.parse(savedSystemPreferences) };
      }

      const savedCacheSettings = localStorage.getItem('docxp_cache_settings');
      if (savedCacheSettings) {
        this.cacheSettings = { ...this.cacheSettings, ...JSON.parse(savedCacheSettings) };
      }

      this.loading = false;
    } catch (error) {
      console.error('Error loading settings:', error);
      this.messageService.add({
        severity: 'warn',
        summary: 'Settings Warning',
        detail: 'Some settings could not be loaded. Using defaults.'
      });
      this.loading = false;
    }
  }

  private saveOriginalSettings() {
    this.originalSettings = {
      apiConfig: { ...this.apiConfig },
      generationSettings: { ...this.generationSettings },
      systemPreferences: { ...this.systemPreferences },
      cacheSettings: { ...this.cacheSettings }
    };
  }

  onSettingsChange() {
    this.unsavedChanges = true;
  }

  saveSettings() {
    this.loading = true;

    try {
      // Save to localStorage
      localStorage.setItem('docxp_api_config', JSON.stringify(this.apiConfig));
      localStorage.setItem('docxp_generation_settings', JSON.stringify(this.generationSettings));
      localStorage.setItem('docxp_system_preferences', JSON.stringify(this.systemPreferences));
      localStorage.setItem('docxp_cache_settings', JSON.stringify(this.cacheSettings));

      // Apply theme changes immediately
      this.applyTheme();

      this.unsavedChanges = false;
      this.saveOriginalSettings();

      this.messageService.add({
        severity: 'success',
        summary: 'Settings Saved',
        detail: 'Your settings have been saved successfully'
      });

      this.loading = false;
    } catch (error) {
      console.error('Error saving settings:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'Save Error',
        detail: 'Failed to save settings. Please try again.'
      });
      this.loading = false;
    }
  }

  private applyTheme() {
    const body = document.body;
    body.classList.remove('light-theme', 'dark-theme');
    
    if (this.systemPreferences.theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      body.classList.add(prefersDark ? 'dark-theme' : 'light-theme');
    } else {
      body.classList.add(`${this.systemPreferences.theme}-theme`);
    }
  }

  resetSettings() {
    this.confirmationService.confirm({
      message: 'Are you sure you want to reset all settings to their default values? This action cannot be undone.',
      header: 'Reset Settings',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.apiConfig = { ...this.originalSettings.apiConfig };
        this.generationSettings = { ...this.originalSettings.generationSettings };
        this.systemPreferences = { ...this.originalSettings.systemPreferences };
        this.cacheSettings = { ...this.originalSettings.cacheSettings };
        
        this.unsavedChanges = true;
        
        this.messageService.add({
          severity: 'info',
          summary: 'Settings Reset',
          detail: 'Settings have been reset to default values. Save to apply changes.'
        });
      }
    });
  }

  testApiConnection() {
    this.loading = true;
    
    // Test actual API connection
    const testUrl = `${this.apiConfig.baseUrl}/health`;
    
    fetch(testUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      signal: AbortSignal.timeout(this.apiConfig.timeout)
    })
    .then(response => {
      if (response.ok) {
        this.messageService.add({
          severity: 'success',
          summary: 'Connection Successful',
          detail: `Successfully connected to ${this.apiConfig.baseUrl}`
        });
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    })
    .catch(error => {
      this.messageService.add({
        severity: 'error',
        summary: 'Connection Failed',
        detail: `Could not connect to the API: ${error.message}`
      });
    })
    .finally(() => {
      this.loading = false;
    });
  }

  clearCache() {
    this.confirmationService.confirm({
      message: 'Are you sure you want to clear all cached data? This may temporarily slow down the application.',
      header: 'Clear Cache',
      icon: 'pi pi-question-circle',
      accept: () => {
        this.loading = true;
        
        // Clear browser caches
        try {
          // Clear localStorage items related to DocXP
          const keysToRemove = [];
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('docxp_')) {
              keysToRemove.push(key);
            }
          }
          keysToRemove.forEach(key => localStorage.removeItem(key));
          
          // Clear sessionStorage
          sessionStorage.clear();
          
          this.messageService.add({
            severity: 'success',
            summary: 'Cache Cleared',
            detail: 'All cached data has been cleared successfully'
          });
        } catch (error) {
          this.messageService.add({
            severity: 'error',
            summary: 'Cache Clear Failed',
            detail: 'Failed to clear cache data'
          });
        } finally {
          this.loading = false;
        }
      }
    });
  }

  exportSettings() {
    const settings = {
      apiConfig: this.apiConfig,
      generationSettings: this.generationSettings,
      systemPreferences: this.systemPreferences,
      cacheSettings: this.cacheSettings,
      exportDate: new Date().toISOString()
    };

    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `docxp-settings-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    window.URL.revokeObjectURL(url);

    this.messageService.add({
      severity: 'info',
      summary: 'Settings Exported',
      detail: 'Settings have been exported successfully'
    });
  }

  importSettings(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedSettings = JSON.parse(e.target?.result as string);
        
        // Validate and merge settings
        if (importedSettings.apiConfig) {
          this.apiConfig = { ...this.apiConfig, ...importedSettings.apiConfig };
        }
        if (importedSettings.generationSettings) {
          this.generationSettings = { ...this.generationSettings, ...importedSettings.generationSettings };
        }
        if (importedSettings.systemPreferences) {
          this.systemPreferences = { ...this.systemPreferences, ...importedSettings.systemPreferences };
        }
        if (importedSettings.cacheSettings) {
          this.cacheSettings = { ...this.cacheSettings, ...importedSettings.cacheSettings };
        }

        this.unsavedChanges = true;

        this.messageService.add({
          severity: 'success',
          summary: 'Settings Imported',
          detail: 'Settings have been imported successfully. Save to apply changes.'
        });
      } catch (error) {
        this.messageService.add({
          severity: 'error',
          summary: 'Import Error',
          detail: 'Invalid settings file. Please check the file format.'
        });
      }
    };
    
    reader.readAsText(file);
    // Clear the input
    event.target.value = '';
  }

  addExcludePattern() {
    this.generationSettings.excludePatterns.push('');
    this.onSettingsChange();
  }

  removeExcludePattern(index: number) {
    this.generationSettings.excludePatterns.splice(index, 1);
    this.onSettingsChange();
  }

  navigateToAWSConfig() {
    if (this.unsavedChanges) {
      this.confirmationService.confirm({
        message: 'You have unsaved changes. Do you want to save them before navigating?',
        header: 'Unsaved Changes',
        icon: 'pi pi-question-circle',
        accept: () => {
          this.saveSettings();
          setTimeout(() => {
            this.router.navigate(['/aws-configuration']);
          }, 500);
        },
        reject: () => {
          this.router.navigate(['/aws-configuration']);
        }
      });
    } else {
      this.router.navigate(['/aws-configuration']);
    }
  }

  // System info methods
  getSystemInfo() {
    return {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      screenResolution: `${screen.width}x${screen.height}`,
      colorDepth: screen.colorDepth,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      localStorage: this.isLocalStorageAvailable(),
      sessionStorage: this.isSessionStorageAvailable()
    };
  }

  private isLocalStorageAvailable(): boolean {
    try {
      const test = '__localStorage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  private isSessionStorageAvailable(): boolean {
    try {
      const test = '__sessionStorage_test__';
      sessionStorage.setItem(test, test);
      sessionStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  showSystemInfo() {
    const info = this.getSystemInfo();
    const infoText = Object.entries(info)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');

    // In a real app, you might show this in a dialog
    alert(`System Information:\n\n${infoText}`);
  }

  getCurrentDate(): string {
    return new Date().toLocaleDateString();
  }

}