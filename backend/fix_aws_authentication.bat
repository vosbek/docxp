@echo off
REM AWS Authentication Fix for DocXP Enterprise (Windows)
REM Fixes AWS SSO credential resolution issues on Windows

echo ===============================================
echo AWS Authentication Fix for DocXP Enterprise
echo ===============================================

echo Step 1: Verifying AWS CLI configuration...
aws --version
if %ERRORLEVEL% neq 0 (
    echo ERROR: AWS CLI not found or not in PATH
    echo Please install AWS CLI v2: https://aws.amazon.com/cli/
    exit /b 1
)

echo Step 2: Checking AWS SSO login status...
aws sts get-caller-identity --profile msh
if %ERRORLEVEL% neq 0 (
    echo AWS SSO login required. Initiating login...
    aws sso login --profile msh
    if %ERRORLEVEL% neq 0 (
        echo ERROR: AWS SSO login failed
        exit /b 1
    )
) else (
    echo AWS SSO login valid
)

echo Step 3: Testing Bedrock access...
aws bedrock list-foundation-models --profile msh --region us-east-1 --query "modelSummaries[?contains(modelId,'anthropic.claude')].{ModelId:modelId,Name:modelName}" --output table
if %ERRORLEVEL% neq 0 (
    echo ERROR: Bedrock access failed. Check IAM permissions.
    echo Required permissions:
    echo - bedrock:ListFoundationModels
    echo - bedrock:InvokeModel
    echo - bedrock:InvokeModelWithResponseStream
    exit /b 1
)

echo Step 4: Setting environment variables...
set AWS_PROFILE=msh
set AWS_REGION=us-east-1
set AWS_DEFAULT_REGION=us-east-1

echo Step 5: Verifying Python boto3 configuration...
python -c "import boto3; session = boto3.Session(profile_name='msh'); print('Profile session created successfully'); sts = session.client('sts'); identity = sts.get_caller_identity(); print(f'Account: {identity.get(\"Account\")}, User: {identity.get(\"Arn\")}')"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python boto3 session creation failed
    exit /b 1
)

echo Step 6: Testing Bedrock runtime access...
python -c "import boto3; session = boto3.Session(profile_name='msh', region_name='us-east-1'); bedrock = session.client('bedrock-runtime'); print('Bedrock runtime client created successfully')"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Bedrock runtime client creation failed
    exit /b 1
)

echo ===============================================
echo AWS Authentication Setup Complete!
echo ===============================================
echo Environment configured for AWS profile: msh
echo Region: us-east-1
echo Bedrock access: Verified
echo
echo You can now start the DocXP backend with:
echo python main.py
echo ===============================================