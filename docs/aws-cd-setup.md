# AWS Elastic Beanstalk CD Setup Guide

Follow these steps **once** to create the AWS infrastructure. After that,
every merge to `main` deploys automatically via the `cd.yml` workflow.

---

## Prerequisites

- An AWS account with billing enabled
- AWS Console access (browser)
- GitHub repository admin access (to add secrets)

---

## Step 1 — Create an IAM User for CI/CD

1. Open the [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Users → Create user**
3. Username: `onboarding-cicd`
4. Select **"Provide user access to the AWS Management Console"** → **No** (skip console)
5. Click **Next → Attach policies directly**
6. Search and attach **all three** of these managed policies:
   - `AWSElasticBeanstalkFullAccess`
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonS3FullAccess`
7. Click **Create user**
8. Open the new user → **Security credentials** tab → **Create access key**
9. Use case: **"Application running outside AWS"**
10. Copy both values — you will add them as GitHub secrets in Step 6.

> **Security note:** These are long-lived credentials. Rotate them every 90 days.
> For a higher-security setup, replace them with OIDC federation later.

---

## Step 2 — Create an ECR Repository

1. Open the [Amazon ECR Console](https://console.aws.amazon.com/ecr/) in **eu-north-1**
2. Click **Create repository**
3. Visibility: **Private**
4. Repository name: `onboarding`
5. Leave all other settings as default → **Create repository**

---

## Step 3 — Create an RDS PostgreSQL Instance

1. Open the [Amazon RDS Console](https://console.aws.amazon.com/rds/) in **eu-north-1**
2. Click **Create database**
3. Settings:
   | Field | Value |
   |-------|-------|
   | Engine | PostgreSQL |
   | Version | 16.x |
   | Template | Free tier (dev) or Production |
   | DB identifier | `onboarding-db` |
   | Master username | `onboarding_app` |
   | Master password | *(generate a strong random password — save it)* |
   | DB instance class | `db.t4g.micro` (free tier) or `db.t3.small` |
   | Storage | 20 GiB gp3 |
   | VPC | **Default VPC** |
   | Public access | **No** |
   | VPC security group | Create new: `rds-onboarding` |
   | Initial database name | `onboarding_prod` |

4. Click **Create database** and wait ~5 min for it to become Available
5. Note the **Endpoint** hostname (e.g. `onboarding-db.xxxx.eu-north-1.rds.amazonaws.com`)

---

## Step 4 — Create the Elastic Beanstalk Application and Environment

1. Open the [Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk/) in **eu-north-1**
2. Click **Create application**
3. Application name: `onboarding`
4. Click **Create environment**
5. Environment tier: **Web server environment**
6. Environment name: `onboarding-prod`
7. Platform: **Docker** (Managed platform, latest version)
8. Application code: **Sample application** (the first real deployment comes from CI)
9. Preset: **Single instance** (or High availability if you need it)
10. Click **Next** through remaining steps with defaults → **Submit**
11. Wait for environment to become **Ready** (~5 min)

---

## Step 5 — Configure EB Security Group to Allow RDS Access

The EB EC2 instance must be allowed to reach the RDS instance.

1. Open the [EC2 Console → Security Groups](https://console.aws.amazon.com/ec2/#SecurityGroups)
2. Find the security group attached to your EB environment (named something like `awseb-...`)
3. Note its **Security Group ID** (e.g. `sg-0abc123`)
4. Open the `rds-onboarding` security group you created in Step 3
5. Click **Edit inbound rules → Add rule**:
   - Type: `PostgreSQL`
   - Port: `5432`
   - Source: *(the EB security group ID from above)*
6. Save rules

---

## Step 6 — Set Environment Variables in Elastic Beanstalk

1. In the EB Console, open `onboarding-prod` → **Configuration**
2. Click **Edit** on the **Environment properties** section
3. Add all of the following:

   | Key | Value |
   |-----|-------|
   | `APP_ENV` | `production` |
   | `DEBUG` | `false` |
   | `SECRET_KEY` | *(run `python -c "import secrets; print(secrets.token_urlsafe(48))"` locally)* |
   | `DB_HOST` | *(RDS endpoint from Step 3)* |
   | `DB_PORT` | `5432` |
   | `DB_NAME` | `onboarding_prod` |
   | `DB_USER` | `onboarding_app` |
   | `DB_PASSWORD` | *(RDS master password from Step 3)* |

4. Click **Apply** and wait for the environment to update

---

## Step 7 — Add GitHub Secrets

1. Open your GitHub repository → **Settings → Secrets and variables → Actions**
2. Click **New repository secret** and add both:

   | Name | Value |
   |------|-------|
   | `AWS_ACCESS_KEY_ID` | *(from Step 1)* |
   | `AWS_SECRET_ACCESS_KEY` | *(from Step 1)* |

3. Create a GitHub **Environment** called `production`:
   - Go to **Settings → Environments → New environment**
   - Name: `production`
   - Add **Required reviewers** if you want manual approval before each deploy
   - (The CD workflow uses `environment: production` to scope the secrets)

---

## Step 8 — Trigger the First Deployment

The CD pipeline runs automatically on every merge to `main`.

To trigger it manually right now:
1. Go to your repo → **Actions → cd**
2. Click **Run workflow → Run workflow**

Watch the workflow run — it will:
1. Build the Docker image
2. Push it to ECR
3. Deploy it to Elastic Beanstalk
4. Wait for the environment to stabilise

Your app will be live at:
```
http://onboarding-prod.eu-north-1.elasticbeanstalk.com
```

---

## Deployment Flow (after setup)

```
Developer opens PR
       ↓
CI workflow runs (lint, security, tests, build, E2E)
       ↓
PR merged to main
       ↓
CD workflow triggers automatically
       ↓
Docker image built → pushed to ECR
       ↓
Dockerrun.aws.json generated with image URI
       ↓
New EB application version created
       ↓
EB environment updated → alembic migrate → uvicorn starts
       ↓
App live at EB URL
```

---

## Checklist Before First Deploy

- [ ] IAM user `onboarding-cicd` created with access keys
- [ ] ECR repository `onboarding` created in eu-north-1
- [ ] RDS instance `onboarding-db` created and Available
- [ ] EB security group whitelisted in RDS inbound rules
- [ ] EB environment variables set (DB_HOST, DB_PASSWORD, SECRET_KEY, etc.)
- [ ] GitHub secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` added
- [ ] GitHub Environment `production` created
