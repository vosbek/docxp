import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'markdown',
  standalone: true
})
export class MarkdownPipe implements PipeTransform {
  transform(value: string): string {
    if (!value) return '';

    // Simple markdown-to-HTML conversion
    let html = value;

    // Headers
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

    // Bold text
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic text
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bullet points - handle multiple list items properly
    html = html.replace(/^[•\-\*] (.*$)/gm, '<li>$1</li>');
    
    // Numbered lists
    html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');
    
    // Wrap consecutive list items in proper list tags
    html = html.replace(/(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/gs, (match) => {
      // Check if this looks like a numbered list (contains digits)
      if (/^\d+\./.test(match.replace(/<[^>]*>/g, ''))) {
        return `<ol>${match}</ol>`;
      }
      return `<ul>${match}</ul>`;
    });

    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraph tags if not already wrapped
    if (!html.startsWith('<')) {
      html = '<p>' + html + '</p>';
    }

    // Emoji support (basic)
    html = html.replace(/:\)/g, '😊');
    html = html.replace(/:\(/g, '😔');

    return html;
  }
}