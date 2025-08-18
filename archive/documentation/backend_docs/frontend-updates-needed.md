# Frontend Updates Required

⚠️ **IMPORTANT**: The following frontend files need to be updated to use the new field names:

## Files to Update

1. **`frontend/src/app/components/aws-configuration/aws-configuration.component.html`**
2. **`frontend/src/app/components/aws-configuration/aws-configuration.component.ts`** 
3. **`frontend/src/app/services/api.service.ts`**

## Required Changes

### Field Name Updates
- `model_id` → `bedrock_model_id`
- `model_count` → `available_models_count`

### Typical Updates Needed

**In TypeScript files:**
```typescript
// Before
interface ModelRequest {
  model_id: string;
}

// After  
interface ModelRequest {
  bedrock_model_id: string;
}

// Before
interface AWSStatus {
  model_count: number;
}

// After
interface AWSStatus {
  available_models_count: number;
}
```

**In HTML templates:**
```html
<!-- Before -->
<input [(ngModel)]="selectedModel" name="model_id">
<span>Models available: {{awsStatus.model_count}}</span>

<!-- After -->
<input [(ngModel)]="selectedModel" name="bedrock_model_id">
<span>Models available: {{awsStatus.available_models_count}}</span>
```

**In API service calls:**
```typescript
// Before
setModel(modelId: string) {
  return this.http.post('/api/configuration/aws/model', { 
    model_id: modelId 
  });
}

// After
setModel(modelId: string) {
  return this.http.post('/api/configuration/aws/model', { 
    bedrock_model_id: modelId 
  });
}
```

These updates will ensure the frontend works correctly with the backend Pydantic fixes.