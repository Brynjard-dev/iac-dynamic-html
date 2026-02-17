## What it does

A serverless service on AWS that serves a simple HTML page. The page displays a dynamic string that can be changed on the fly without touching the infrastructure or redeploying anything.

```
GET /  -->  <h1>The saved string is whatever you set</h1>
PUT /string  -->  updates the string
```

## Architecture

```
Browser --> API Gateway (HTTP API) --> Lambda (Python 3.12) --> SSM Parameter Store
```

Three AWS services, that's it:

- **API Gateway HTTP API** handles routing. Two routes: `GET /` to serve the page, `PUT /string` to update the value.
- **Lambda** runs a small Python function that reads or writes the string. No external dependencies -- just boto3 which comes bundled with the Lambda runtime.
- **SSM Parameter Store** holds the dynamic string. It's basically a key-value store built into AWS.

Everything is provisioned with Terraform.

## Options I considered

### Where to store the string

| Option | Verdict |
|--------|---------|
| SSM Parameter Store | Went with this. Free, simple, purpose-built for config values. No schema or table to set up. |
| DynamoDB | Would work fine but feels like overkill for storing a single string. You'd need to define a table, pick a partition key, etc. |
| S3 | Technically possible - store a text file and read it. But S3 is designed for files, not config values. Latency is slightly worse too. |

### How to expose the endpoint

| Option | Verdict |
|--------|---------|
| API Gateway HTTP API | Went with this. Cheaper than REST API, simpler config, supports the routing I need. |
| API Gateway REST API | More features (request validation, caching, usage plans) but none of that is needed here. More Terraform to write for no benefit. |
| Lambda Function URL | The simplest option, but it doesn't support routing. I'd need to handle both GET and PUT on the same path, which is a bit awkward. |
| ALB + ECS/Fargate | Way too heavy for serving a single HTML page. Costs more, takes longer to provision, more moving parts. |

## Key decisions worth calling out

**`lifecycle { ignore_changes = [value] }` on the SSM parameter.** This is the most important Terraform detail. Without it, running `terraform apply` after updating the string would reset it back to the default value. The `ignore_changes` block tells Terraform "I'll set this once, but after that leave it alone."

**No build step.** The Lambda handler is a single Python file with no dependencies beyond boto3. Terraform's `archive_file` data source zips it up automatically. No Docker, no layers, no packaging scripts.

**$default stage.** API Gateway supports named stages like `/prod` or `/dev`, but using the `$default` stage gives a clean URL without any prefix. Keeps things simple.

## How to update the string

Three ways, pick whichever:

```bash
# via the API
curl -X PUT https://your-api-url/string \
  -H "Content-Type: application/json" \
  -d '{"value": "new string here"}'

# via the helper script
python scripts/update_string.py "new string here"

# via AWS CLI or powershell 
aws ssm put-parameter --name "/dynamic-html/dynamic-string" --value "Testing from AWS CLI" --overwrite

# via git bash
MSYS_NO_PATHCONV=1 aws ssm put-parameter --name '/dynamic-html/dynamic-string' --type String --value 'Testing from Git bash' --overwrite --region us-east-1
```

## What I'd do with more time

**Authentication on the PUT endpoint.** Right now anyone who knows the URL can update the string. In a real setup I'd add an API key or IAM auth on the write route while keeping the read route public.

**CloudFront in front of API Gateway.** Adds caching (so Lambda doesn't get hit on every single page view), supports custom domains with HTTPS via ACM, and gives you edge locations worldwide.

**Custom domain.** A Route53 alias pointing to CloudFront or API Gateway, with an ACM certificate. Something like `dynamic.example.com` instead of the auto-generated API Gateway URL.

**Input sanitization.** The dynamic string gets dropped straight into HTML. If someone sets it to `<script>alert('xss')</script>` that would execute in the browser. I'd HTML-escape the value before rendering.

**Monitoring.** CloudWatch alarms on Lambda errors and latency. Maybe a dashboard showing request counts and P99 response times.

**CI/CD.** A GitHub Actions workflow that runs `terraform plan` on PRs and `terraform apply` on merge to main. With a remote state backend (S3 + DynamoDB for locking) so multiple people can work on it safely.

**Terraform tests.** Using the built-in `terraform test` framework to validate the module produces the expected resources and outputs.
