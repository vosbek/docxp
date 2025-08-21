import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, Router } from '@angular/router';
import { PrimeNGConfig } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { SidebarModule } from 'primeng/sidebar';
import { MenubarModule } from 'primeng/menubar';
import { MenuItem } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    ButtonModule,
    SidebarModule,
    MenubarModule,
    AvatarModule,
    BadgeModule,
    RippleModule,
    ToastModule
  ],
  providers: [MessageService],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'DocXP';
  sidebarVisible = false;
  menuItems: MenuItem[] = [];

  constructor(
    private primengConfig: PrimeNGConfig,
    private messageService: MessageService,
    private router: Router
  ) {}

  ngOnInit() {
    this.primengConfig.ripple = true;
    this.initializeMenu();
  }

  initializeMenu() {
    this.menuItems = [
      {
        label: 'AWS Configuration',
        icon: 'pi pi-key',
        routerLink: '/aws-configuration'
      },
      {
        label: 'Dashboard',
        icon: 'pi pi-home',
        routerLink: '/dashboard'
      },
      {
        label: 'Generate',
        icon: 'pi pi-bolt',
        routerLink: '/generate'
      },
      {
        label: 'AI Chat',
        icon: 'pi pi-comments',
        routerLink: '/chat'
      },
      {
        label: 'V1 Search',
        icon: 'pi pi-search',
        routerLink: '/v1-search'
      },
      {
        label: 'Repositories',
        icon: 'pi pi-folder',
        routerLink: '/repositories'
      },
      {
        label: 'History',
        icon: 'pi pi-history',
        routerLink: '/history'
      },
      {
        label: 'Analytics',
        icon: 'pi pi-chart-line',
        routerLink: '/analytics'
      },
      {
        label: 'Settings',
        icon: 'pi pi-cog',
        routerLink: '/settings'
      }
    ];
  }

  toggleSidebar() {
    this.sidebarVisible = !this.sidebarVisible;
  }
  
  navigateToRoute(route?: string) {
    if (route) {
      this.router.navigate([route]);
      this.sidebarVisible = false;
    }
  }
  
  showImportMessage() {
    this.messageService.add({
      severity: 'info',
      summary: 'Import Repository',
      detail: 'Repository import feature coming soon'
    });
    this.sidebarVisible = false;
  }
}
