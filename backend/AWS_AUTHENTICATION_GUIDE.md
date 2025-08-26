# AWS Authentication Setup Guide for DocXP Enterprise

## Problem Summary
AWS Bedrock authentication failing with "The security token included in the request is invalid" despite valid AWS SSO credentials.

## Root Cause
1. **Windows SSO Token Resolution**: AWS SSO credentials on Windows require specific configuration for boto3
2. **Session Token Propagation**: Temporary credentials from SSO not properly handled by application
3. **Bedrock Permissions**: Profile may lack specific Bedrock IAM permissions

## Enterprise Solution

### Step 1: Verify AWS CLI Configuration

```bash
# Check AWS CLI version (must be v2+)
aws --version

# Verify profile configuration
aws configure list --profile msh

# Test SSO login
aws sso login --profile msh

# Verify credentials work
aws sts get-caller-identity --profile msh
```

### Step 2: Configure AWS Profile for Bedrock

Ensure your `~/.aws/config` includes:

```ini
[profile msh]
sso_start_url = https://your-org.awsapps.com/start
sso_region = us-east-1
sso_account_id = 123456789012
sso_role_name = YourRoleName
region = us-east-1
output = json

# Enable CLI v2 features
cli_pager = 
cli_auto_prompt = off
```

### Step 3: Verify Bedrock Permissions

Test Bedrock access:
```bash
aws bedrock list-foundation-models --profile msh --region us-east-1
```

Required IAM permissions for your SSO role:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:ListFoundationModels",
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:GetFoundationModel"
            ],
            "Resource": "*"
        }
    ]
}
```

### Step 4: Environment Configuration

Update your `.env.enterprise` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=msh
AWS_DEFAULT_REGION=us-east-1

# Windows-specific AWS configuration
AWS_CONFIG_FILE=C:\Users\%USERNAME%\.aws\config
AWS_SHARED_CREDENTIALS_FILE=C:\Users\%USERNAME%\.aws\credentials

# AWS SDK retry configuration
AWS_MAX_ATTEMPTS=3
AWS_RETRY_MODE=adaptive
AWS_API_TIMEOUT=30

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
CHAT_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Step 5: Run Automated Fix

Execute the Windows batch script:
```cmd
cd backend
fix_aws_authentication.bat
```

### Step 6: Manual Verification

Test the configuration:
```python
import boto3
import os

# Test 1: Profile session
os.environ['AWS_PROFILE'] = 'msh'
session = boto3.Session(profile_name='msh', region_name='us-east-1')
sts = session.client('sts')
identity = sts.get_caller_identity()
print(f"Account: {identity['Account']}, User: {identity['Arn']}")

# Test 2: Bedrock client
bedrock = session.client('bedrock-runtime')
print("Bedrock client created successfully")

# Test 3: List models
bedrock_control = session.client('bedrock')
models = bedrock_control.list_foundation_models()
claude_models = [m for m in models['modelSummaries'] if 'anthropic.claude' in m['modelId']]
print(f"Found {len(claude_models)} Claude models")
```

## Enterprise Deployment Considerations

### Production Environment
1. **Service Accounts**: Use IAM roles instead of user SSO for production
2. **Cross-Account Access**: Configure assume role patterns for multi-account setups
3. **Credential Rotation**: Implement automated credential refresh for long-running services

### Security Best Practices
1. **Least Privilege**: Grant minimum required Bedrock permissions
2. **Logging**: Enable CloudTrail for Bedrock API calls
3. **Network**: Use VPC endpoints for Bedrock access if required

### Monitoring
- Set up CloudWatch alarms for authentication failures
- Monitor credential expiration times
- Track Bedrock API usage and costs

## Troubleshooting

### Common Issues

1. **"Token has expired"**
   - Run: `aws sso login --profile msh`
   - Restart application after login

2. **"Access denied to Bedrock"**
   - Verify IAM permissions
   - Check service availability in your region

3. **"Profile not found"**
   - Verify `~/.aws/config` file
   - Check profile name spelling

4. **"Region not available"**
   - Bedrock is not available in all regions
   - Use: us-east-1, us-west-2, or eu-west-1

### Debug Commands
```bash
# View effective AWS configuration
aws configure list --profile msh

# Test different AWS services
aws sts get-caller-identity --profile msh
aws bedrock list-foundation-models --profile msh --region us-east-1

# Debug boto3 credential resolution
python -c "import boto3; print(boto3.Session(profile_name='msh').get_credentials())"
```

## Support
For enterprise support, ensure your organization has:
- AWS Enterprise Support plan
- Bedrock service quota increases if needed
- Appropriate compliance approvals for AI services