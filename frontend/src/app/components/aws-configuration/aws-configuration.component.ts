import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TabViewModule } from 'primeng/tabview';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';
import { TagModule } from 'primeng/tag';
import { MessageService } from 'primeng/api';

import { ApiService } from '../../services/api.service';

interface AWSModel {
  id: string;
  name: string;
  provider: string;
  description: string;
}

interface AWSProfile {
  name: string;
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
    FormsModule,
    ReactiveFormsModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TabViewModule,
    MessageModule,
    ToastModule,
    ProgressSpinnerModule,
    DividerModule,
    TagModule
  ],
  providers: [MessageService],
  templateUrl: './aws-configuration.component.html',
  styleUrls: ['./aws-configuration.component.scss']
})
export class AwsConfigurationComponent implements OnInit {
  @Output() configurationComplete = new EventEmitter<{success: boolean, message: string}>();

  // Forms
  accessKeysForm: FormGroup;
  ssoProfileForm: FormGroup;
  
  // State
  activeTab: number = 0;
  loading: boolean = false;
  testing: boolean = false;
  configuring: boolean = false;
  
  // Data
  awsProfiles: string[] = [];
  availableModels: AWSModel[] = [];
  selectedModel: string = 'anthropic.claude-v2';
  awsStatus: AWSStatus | null = null;
  
  // Regions
  regions = [
    { label: 'US East 1 (N. Virginia)', value: 'us-east-1' },
    { label: 'US East 2 (Ohio)', value: 'us-east-2' },
    { label: 'US West 1 (N. California)', value: 'us-west-1' },
    { label: 'US West 2 (Oregon)', value: 'us-west-2' },
    { label: 'Europe (Ireland)', value: 'eu-west-1' },
    { label: 'Europe (London)', value: 'eu-west-2' },
    { label: 'Europe (Frankfurt)', value: 'eu-central-1' },
    { label: 'Asia Pacific (Tokyo)', value: 'ap-northeast-1' },
    { label: 'Asia Pacific (Singapore)', value: 'ap-southeast-1' },
    { label: 'Asia Pacific (Sydney)', value: 'ap-southeast-2' }
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private messageService: MessageService
  ) {
    this.accessKeysForm = this.fb.group({
      aws_access_key_id: ['', Validators.required],
      aws_secret_access_key: ['', Validators.required],
      aws_session_token: [''],
      aws_region: ['us-east-1', Validators.required]
    });

    this.ssoProfileForm = this.fb.group({
      aws_profile: ['', Validators.required],
      aws_region: ['us-east-1', Validators.required]
    });
  }

  ngOnInit() {
    this.loadAWSStatus();
    this.loadAWSProfiles();
    this.loadAvailableModels();
  }

  loadAWSStatus() {
    this.apiService.getAWSStatus().subscribe({
      next: (status: AWSStatus) => {
        this.awsStatus = status;
        if (status.connected) {
          this.messageService.add({
            severity: 'success',
            summary: 'AWS Connected',
            detail: `Connected to account ${status.account_id} with ${status.available_models_count} models`
          });
        }
      },
      error: (error) => {
        console.error('Failed to load AWS status:', error);
      }
    });
  }

  loadAWSProfiles() {
    this.loading = true;
    this.apiService.getAWSProfiles().subscribe({
      next: (response: any) => {
        if (response.success) {
          this.awsProfiles = response.profiles;
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load AWS profiles:', error);
        this.loading = false;
      }
    });
  }

  loadAvailableModels() {
    this.apiService.getAvailableModels().subscribe({
      next: (response: any) => {
        if (response.success) {
          this.availableModels = response.models;
          this.selectedModel = response.current_model || 'anthropic.claude-v2';
        }
      },
      error: (error) => {
        console.error('Failed to load models:', error);
      }
    });
  }

  testAccessKeysCredentials() {
    if (this.accessKeysForm.invalid) {
      this.markFormGroupTouched(this.accessKeysForm);
      return;
    }

    this.testing = true;
    const formData = this.accessKeysForm.value;

    this.apiService.testAWSCredentials({
      auth_method: 'access_keys',
      ...formData
    }).subscribe({
      next: (response: any) => {
        this.testing = false;
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Credentials Valid',
            detail: `Connected to AWS account ${response.account_id} with ${response.available_models_count} models`
          });
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Credentials Invalid',
            detail: response.message
          });
        }
      },
      error: (error) => {
        this.testing = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Test Failed',
          detail: error.error?.detail || 'Failed to test credentials'
        });
      }
    });
  }

  testSSProfileCredentials() {
    if (this.ssoProfileForm.invalid) {
      this.markFormGroupTouched(this.ssoProfileForm);
      return;
    }

    this.testing = true;
    const formData = this.ssoProfileForm.value;

    this.apiService.testAWSCredentials({
      auth_method: 'sso_profile',
      ...formData
    }).subscribe({
      next: (response: any) => {
        this.testing = false;
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Profile Valid',
            detail: `Connected to AWS account ${response.account_id} with ${response.available_models_count} models`
          });
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Profile Invalid',
            detail: response.message
          });
        }
      },
      error: (error) => {
        this.testing = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Test Failed',
          detail: error.error?.detail || 'Failed to test profile'
        });
      }
    });
  }

  configureAccessKeys() {
    if (this.accessKeysForm.invalid) {
      this.markFormGroupTouched(this.accessKeysForm);
      return;
    }

    this.configuring = true;
    const formData = this.accessKeysForm.value;

    this.apiService.configureAWS({
      auth_method: 'access_keys',
      ...formData
    }).subscribe({
      next: (response: any) => {
        this.configuring = false;
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Configuration Saved',
            detail: 'AWS credentials configured successfully'
          });
          this.loadAWSStatus();
          this.configurationComplete.emit({success: true, message: 'AWS credentials configured'});
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Configuration Failed',
            detail: response.message
          });
        }
      },
      error: (error) => {
        this.configuring = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Configuration Failed',
          detail: error.error?.detail || 'Failed to configure credentials'
        });
      }
    });
  }

  configureSSProfile() {
    if (this.ssoProfileForm.invalid) {
      this.markFormGroupTouched(this.ssoProfileForm);
      return;
    }

    this.configuring = true;
    const formData = this.ssoProfileForm.value;

    this.apiService.configureAWS({
      auth_method: 'sso_profile',
      ...formData
    }).subscribe({
      next: (response: any) => {
        this.configuring = false;
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Configuration Saved',
            detail: 'AWS profile configured successfully'
          });
          this.loadAWSStatus();
          this.configurationComplete.emit({success: true, message: 'AWS profile configured'});
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Configuration Failed',
            detail: response.message
          });
        }
      },
      error: (error) => {
        this.configuring = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Configuration Failed',
          detail: error.error?.detail || 'Failed to configure profile'
        });
      }
    });
  }

  setBedrockModel() {
    if (!this.selectedModel) return;

    this.apiService.setBedrockModel(this.selectedModel).subscribe({
      next: (response: any) => {
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Model Updated',
            detail: `Model set to ${this.selectedModel}`
          });
        }
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Model Update Failed',
          detail: error.error?.detail || 'Failed to set model'
        });
      }
    });
  }

  private markFormGroupTouched(formGroup: FormGroup) {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      if (control) {
        control.markAsTouched();
      }
    });
  }

  getConnectionStatusSeverity(): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    if (!this.awsStatus) return 'secondary';
    return this.awsStatus.connected ? 'success' : 'danger';
  }

  getConnectionStatusText(): string {
    if (!this.awsStatus) return 'Unknown';
    if (this.awsStatus.connected) {
      return `Connected (${this.awsStatus.account_id})`;
    }
    return 'Not Connected';
  }

  // Helper methods for template bindings
  getAwsProfileOptions(): any[] {
    return this.awsProfiles.map(p => ({label: p, value: p}));
  }

  getSelectedModelName(): string {
    const model = this.availableModels.find(m => m.id === this.selectedModel);
    return model ? model.name : '';
  }

  getSelectedModelProvider(): string {
    const model = this.availableModels.find(m => m.id === this.selectedModel);
    return model ? model.provider : '';
  }
}