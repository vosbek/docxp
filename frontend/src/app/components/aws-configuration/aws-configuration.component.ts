import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

// PrimeNG Imports
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

import { ApiService } from '../../services/api.service';

interface AWSModel {
  id: string;
  name: string;
  provider: string;
  description: string;
}

interface AWSStatus {
  connected: boolean;
  error?: string;
  account_id?: string;
  region: string;
  auth_method: string;
  available_models_count: number;
}

@Component({
  selector: 'app-aws-configuration',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    ToastModule
  ],
  providers: [MessageService],
  templateUrl: './aws-configuration.component.html',
  styleUrls: ['./aws-configuration.component.scss']
})
export class AwsConfigurationComponent implements OnInit {
  @Output() configurationComplete = new EventEmitter<{success: boolean, message: string}>();

  // State
  loading: boolean = false;
  
  // Data
  currentModel: AWSModel | null = null;
  awsStatus: AWSStatus | null = null;

  constructor(
    private apiService: ApiService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.refreshStatus();
  }

  refreshStatus() {
    this.loadAWSStatus();
    this.loadCurrentModelInfo();
  }

  loadAWSStatus() {
    this.loading = true;
    this.apiService.getAWSStatus().subscribe({
      next: (status: AWSStatus) => {
        this.awsStatus = status;
        this.loading = false;
        
        if (status.connected) {
          this.messageService.add({
            severity: 'success',
            summary: 'AWS Connected',
            detail: `Connected to account ${status.account_id} with ${status.available_models_count} models`,
            life: 3000
          });
        }
      },
      error: (error) => {
        console.error('Failed to load AWS status:', error);
        this.loading = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Status Check Failed',
          detail: 'Unable to check AWS connection status',
          life: 5000
        });
      }
    });
  }

  loadCurrentModelInfo() {
    this.apiService.getCurrentModelInfo().subscribe({
      next: (response: any) => {
        if (response.success) {
          this.currentModel = response.model;
        }
      },
      error: (error) => {
        console.error('Failed to load current model info:', error);
      }
    });
  }

  // Template helper methods
  getStatusCardClass(): string {
    if (!this.awsStatus) return 'status-unknown';
    return this.awsStatus.connected ? 'status-connected' : 'status-error';
  }

  getStatusIcon(): string {
    if (!this.awsStatus) return 'pi pi-question-circle';
    return this.awsStatus.connected ? 'pi pi-check-circle' : 'pi pi-times-circle';
  }

  getStatusTitle(): string {
    if (!this.awsStatus) return 'Checking Connection...';
    return this.awsStatus.connected ? 'AWS Connected' : 'Connection Failed';
  }

  getStatusMessage(): string {
    if (!this.awsStatus) return 'Loading AWS connection status...';
    
    if (this.awsStatus.connected) {
      return `Successfully connected to AWS account ${this.awsStatus.account_id || 'Unknown'}`;
    } else {
      return 'AWS connection failed. Check your .env configuration.';
    }
  }

  getAuthMethodDisplay(): string {
    if (!this.awsStatus) return 'N/A';
    
    switch (this.awsStatus.auth_method) {
      case 'access_keys':
        return 'Access Keys';
      case 'sso_profile':
        return 'SSO Profile';
      default:
        return this.awsStatus.auth_method || 'Unknown';
    }
  }
}