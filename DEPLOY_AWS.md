# Deploy VibeCheck to AWS (Using AWS Academy Credits)

Deploy your Dockerized Flask app to AWS using Elastic Beanstalk.

## Prerequisites

1. **AWS Academy Access**
   - Log into AWS Academy Learner Lab
   - Start your lab session (you have $50 credit)

2. **Install AWS CLI and EB CLI**
   ```bash
   # Install AWS CLI
   brew install awscli

   # Install EB CLI
   pip install awsebcli
   ```

3. **Configure AWS Credentials**
   - In AWS Academy, click "AWS Details"
   - Copy your credentials (Access Key, Secret Key, Session Token)

   ```bash
   # Configure AWS CLI
   aws configure
   # Enter your Access Key ID
   # Enter your Secret Access Key
   # Region: us-east-1 (or your preferred region)
   # Output: json

   # Set session token (AWS Academy requires this)
   export AWS_SESSION_TOKEN="your-session-token-here"
   ```

## Deployment Steps

### Option 1: Elastic Beanstalk (Recommended - Easiest)

1. **Initialize EB application**
   ```bash
   eb init -p docker vibecheck --region us-east-1
   ```

2. **Create environment** (choose t3.small for 2GB RAM)
   ```bash
   eb create vibecheck-env \
     --instance-type t3.small \
     --single \
     --timeout 30
   ```

3. **Deploy**
   ```bash
   eb deploy
   ```

4. **Open your app**
   ```bash
   eb open
   ```

5. **Check status and logs**
   ```bash
   eb status
   eb logs
   ```

### Option 2: ECS (More control, slightly more complex)

1. **Build and push to ECR**
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name vibecheck

   # Get login credentials
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

   # Build and tag
   docker build -f docker/app/Dockerfile -t vibecheck .
   docker tag vibecheck:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/vibecheck:latest

   # Push to ECR
   docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/vibecheck:latest
   ```

2. **Create ECS cluster via AWS Console**
   - Go to ECS → Create Cluster → EC2 Linux + Networking
   - Instance type: t3.small (2GB RAM)
   - Create task definition with your ECR image
   - Create service

### Option 3: EC2 + Docker Compose (Most control)

1. **Launch EC2 instance**
   - AMI: Amazon Linux 2023
   - Instance type: t3.small (2GB RAM, ~$15/month)
   - Security group: Allow inbound on port 80 and 8080

2. **SSH into instance**
   ```bash
   ssh -i your-key.pem ec2-user@<public-ip>
   ```

3. **Install Docker**
   ```bash
   sudo yum update -y
   sudo yum install docker git -y
   sudo service docker start
   sudo usermod -a -G docker ec2-user

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Clone and run**
   ```bash
   git clone https://github.com/YOUR_USERNAME/VibeCheck.git
   cd VibeCheck
   docker-compose up -d
   ```

## Cost Breakdown (with $50 credit)

| Instance Type | RAM | vCPU | Cost/month | Months with $50 |
|--------------|-----|------|------------|-----------------|
| **t3.micro** | 1GB | 2 | ~$7 | 7 months ⚠️ (might OOM) |
| **t3.small** | 2GB | 2 | ~$15 | 3 months ✅ (recommended) |
| **t3.medium** | 4GB | 2 | ~$30 | 1.5 months |

**Recommendation**: Use **t3.small** (2GB RAM) - Perfect balance of cost and performance.

## Monitoring Your Credit

```bash
# Check your current usage
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-12-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## Troubleshooting

**EB deployment fails?**
```bash
eb logs
# Look for OOM errors or timeout issues
```

**App running out of memory?**
- Upgrade to t3.medium (4GB RAM)
- Or optimize: reduce Gunicorn threads, disable CLIP model

**Session token expired?**
- AWS Academy sessions expire after 4 hours
- Restart lab and get new credentials

**Want HTTPS?**
- EB automatically provides HTTPS endpoint
- Or use AWS Certificate Manager + Load Balancer (free!)

## Cleanup (to save credits)

```bash
# Terminate environment
eb terminate vibecheck-env

# Delete application
eb delete vibecheck
```

## Tips to Maximize Your $50

1. **Use t3.small** - Best cost/performance ratio
2. **Stop when not demoing** - Stop EC2 instance to save money (only pay for storage)
3. **Set billing alerts** - Get notified at $10, $25, $40
4. **Use spot instances** - 70% cheaper but can be terminated
5. **Single instance** - No load balancer needed for demo app

Your $50 should last 3-4 months with t3.small running 24/7!
