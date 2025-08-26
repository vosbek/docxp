import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { ChatService } from '../../services/chat.service';
import { ApiService, RepositoryInfo } from '../../services/api.service';
import { MarkdownPipe } from '../../shared/pipes/markdown.pipe';

export interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant';
  timestamp: Date;
  isLoading?: boolean;
  metadata?: {
    repositoryName?: string;
    fileReferences?: string[];
    codeSnippets?: any[];
  };
}

export interface Repository {
  id: string;
  name: string;
  technology: string;
  status: 'indexed' | 'processing' | 'error';
  lastIndexed?: Date;
  description?: string;
}

@Component({
  selector: 'app-chat-interface',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MarkdownPipe
  ],
  templateUrl: './chat-interface.component.html',
  styleUrls: ['./chat-interface.component.scss']
})
export class ChatInterfaceComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  currentMessage = '';
  messages: ChatMessage[] = [];
  isLoading = false;
  
  // Repository management
  repositoryFilter = '';
  selectedRepositories: Repository[] = [];
  availableRepositories: Repository[] = [];
  
  suggestedQuestions = [
    'Show me all repositories using legacy authentication',
    'Which repos connect to the CUSTOMER_ACCOUNTS Oracle table?',
    'Find all Struts actions that handle payment processing',
    'What are the migration risks for the UserManagement service?',
    'Generate a modernization plan for CORBA interfaces'
  ];

  private destroy$ = new Subject<void>();

  constructor(
    private chatService: ChatService,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    this.initializeWelcomeMessage();
    this.loadRepositories();
  }

  private loadRepositories() {
    this.apiService.listRepositories().subscribe({
      next: (repositories: RepositoryInfo[]) => {
        this.availableRepositories = repositories.map(repo => ({
          id: repo.name,
          name: repo.name,
          technology: this.detectTechnology(repo.languages),
          status: 'indexed' as const,
          lastIndexed: new Date(),
          description: `${repo.total_files} files, ${repo.total_lines} lines`
        }));
      },
      error: (error) => {
        console.error('Failed to load repositories:', error);
        // No hardcoded fallback - require proper backend connection
        this.availableRepositories = [];
      }
    });
  }

  private detectTechnology(languages: { [key: string]: number }): string {
    if (!languages || Object.keys(languages).length === 0) {
      return 'Unknown';
    }
    
    const primaryLanguage = Object.keys(languages)[0];
    const languageMap: { [key: string]: string } = {
      'Java': 'Java/Spring',
      'JavaScript': 'JavaScript/Node.js',
      'TypeScript': 'TypeScript/Angular',
      'Python': 'Python',
      'C#': 'C#/.NET',
      'C++': 'C++',
      'Go': 'Go',
      'Rust': 'Rust'
    };
    
    return languageMap[primaryLanguage] || primaryLanguage;
  }

  ngAfterViewInit() {
    this.focusInput();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get filteredRepositories(): Repository[] {
    if (!this.repositoryFilter.trim()) {
      return this.availableRepositories.filter(repo => 
        !this.selectedRepositories.find(selected => selected.id === repo.id)
      );
    }
    
    const filter = this.repositoryFilter.toLowerCase();
    return this.availableRepositories.filter(repo => 
      !this.selectedRepositories.find(selected => selected.id === repo.id) &&
      (repo.name.toLowerCase().includes(filter) || 
       repo.technology.toLowerCase().includes(filter))
    );
  }

  private initializeWelcomeMessage() {
    const welcomeMessage: ChatMessage = {
      id: this.generateId(),
      content: `👋 **Welcome to DocXP AI Assistant**

I'm here to help you analyze your legacy codebase and plan your migration to modern technologies. I can:

• **Analyze repository structures** and dependencies
• **Find patterns** across multiple repositories  
• **Identify migration risks** and recommend strategies
• **Locate specific code** like Struts actions, CORBA interfaces, or Oracle table usage
• **Generate modernization plans** for your enterprise systems

What would you like to explore today?`,
      type: 'assistant',
      timestamp: new Date()
    };

    this.messages = [welcomeMessage];
  }

  async sendMessage() {
    if (!this.currentMessage.trim() || this.isLoading) return;

    const userMessage: ChatMessage = {
      id: this.generateId(),
      content: this.currentMessage,
      type: 'user',
      timestamp: new Date()
    };

    this.messages.push(userMessage);
    this.currentMessage = '';
    this.isLoading = true;

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: this.generateId(),
      content: '',
      type: 'assistant',
      timestamp: new Date(),
      isLoading: true
    };
    this.messages.push(loadingMessage);

    this.scrollToBottom();

    try {
      const response = await this.chatService.sendMessage(userMessage.content);
      
      // Remove loading message and add response
      this.messages.pop();
      
      const assistantMessage: ChatMessage = {
        id: this.generateId(),
        content: response.content,
        type: 'assistant',
        timestamp: new Date(),
        metadata: response.metadata
      };

      this.messages.push(assistantMessage);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Remove loading message and add error
      this.messages.pop();
      
      const errorMessage: ChatMessage = {
        id: this.generateId(),
        content: '❌ Sorry, I encountered an error processing your request. Please try again.',
        type: 'assistant',
        timestamp: new Date()
      };

      this.messages.push(errorMessage);
    } finally {
      this.isLoading = false;
      this.scrollToBottom();
      this.focusInput();
    }
  }

  useSuggestedQuestion(question: string) {
    this.currentMessage = question;
    this.sendMessage();
  }

  onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  refreshRepositories() {
    console.log('Refreshing repositories...');
    
    // Clear current repositories and reload
    this.availableRepositories = [];
    this.selectedRepositories = [];
    
    // Update chat service context
    this.chatService.updateContext({
      repositoryIds: []
    });
    
    // Reload repositories from API
    this.loadRepositories();
    
    // Show feedback message
    const refreshMessage: ChatMessage = {
      id: this.generateId(),
      content: '🔄 **Repositories refreshed** - Updated repository list from server.',
      type: 'assistant',
      timestamp: new Date()
    };
    
    this.messages.push(refreshMessage);
    this.scrollToBottom();
  }

  clearChat() {
    this.messages = [];
    this.initializeWelcomeMessage();
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.messagesContainer) {
        const element = this.messagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }

  private focusInput() {
    setTimeout(() => {
      if (this.messageInput) {
        this.messageInput.nativeElement.focus();
      }
    }, 100);
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  formatTimestamp(timestamp: Date): string {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  toggleRepository(repository: Repository) {
    const index = this.selectedRepositories.findIndex(repo => repo.id === repository.id);
    
    if (index > -1) {
      // Remove from selected
      this.selectedRepositories.splice(index, 1);
    } else {
      // Add to selected (only if indexed)
      if (repository.status === 'indexed') {
        this.selectedRepositories.push(repository);
      }
    }
    
    // Update chat service context
    this.chatService.updateContext({
      repositoryIds: this.selectedRepositories.map(repo => repo.id)
    });
  }
}