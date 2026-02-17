# Solution

## My solution and the available options

I built a serverless service on AWS that serves an HTML page with a dynamic string. Three services working together:

```
Browser --> API Gateway (HTTP API) --> Lambda (Python 3.12) --> SSM Parameter Store
```

- **API Gateway HTTP API** provides the public URL and routes requests. `GET /` serves the page, `PUT /string` updates the value.
- **Lambda** runs a Python function that reads or writes the string. No external dependencies since boto3 comes bundled with the Lambda runtime, so there's no build step.
- **SSM Parameter Store** holds the dynamic string. It's a key-value store built into AWS.

The whole thing is provisioned with Terraform. Ten resources, one data source, about 100 lines of HCL.

To update the string without redeploying, there are three options:

```bash
# hit the API directly
curl -X PUT https://your-api-url/string \
  -H "Content-Type: application/json" \
  -d '{"value": "new string here"}'

# use the helper script
python scripts/update_string.py "new string here"

# use the AWS CLI
aws ssm put-parameter --name "/dynamic-html/dynamic-string" --value "new string here" --overwrite
```

### Other options I considered

**For storing the string:**

| Option | Why I did or didn't use it |
|--------|---------------------------|
| SSM Parameter Store | Went with this. Free, purpose-built for config values. No schema or table to set up. Simple get/put API. |
| DynamoDB | Would work, but overkill for a single string. You'd need to define a table, pick a partition key, handle read/write capacity. Better suited for structured data with multiple records. |
| S3 | Possible - store a text file and read it back. But S3 is designed for files, not config values. The API is more verbose and latency is slightly higher. |

**For serving the endpoint:**

| Option | Why I did or didn't use it |
|--------|---------------------------|
| API Gateway HTTP API | Went with this. Cheaper than REST API, lower latency, simpler config. Supports the routing I need. |
| API Gateway REST API | More features (request validation, built-in caching, usage plans, WAF integration) but none of that is needed here. More Terraform to write for no benefit. |
| Lambda Function URL | The simplest option - a URL directly on the function, no API Gateway needed. But it doesn't support routing, so I'd have to handle GET and PUT on the same path, which is awkward. |
| ALB + ECS/Fargate | Way too heavy for a single HTML page. You'd need to manage containers, scaling, health checks. Costs money even at zero traffic. |


## The reasons behind my decisions

**SSM Parameter Store over a database.** The whole point of the challenge is storing one string. SSM is literally designed for this, it's a key-value store for configuration. Free for standard parameters, no infrastructure to manage beyond the parameter itself. DynamoDB would be my choice if I needed to store structured data or multiple records, but for a single value it adds unnecessary complexity.

**`lifecycle { ignore_changes = [value] }` on the SSM parameter.** This is the most important Terraform detail in the project. Terraform normally tracks everything about the resources it creates. If you change a value outside of Terraform (through the API, CLI, etc.), the next `terraform apply` would "drift correct" and reset it. The `ignore_changes` block tells Terraform to create and own the parameter, but leave the value alone after that. Without this, updating the string at runtime would be pointless since Terraform would overwrite it on the next apply.

**No build step.** The Lambda handler is a single Python file. The only dependency is boto3, which comes pre-installed in the Lambda Python runtime. Terraform's `archive_file` data source zips the file automatically. No Docker, no layers, no Makefile, no CI pipeline needed to deploy. This keeps the project simple and easy to understand.

**API Gateway HTTP API over REST API.** HTTP APIs are roughly cheaper, have lower latency, and require less configuration. REST APIs have more enterprise features (caching, WAF, request validation) but none of that is relevant here. Simpler is better when the extra features aren't needed.

**`$default` stage.** API Gateway supports named stages like `/prod` or `/dev`, which add a prefix to the URL. Using the `$default` stage gives a clean URL without any prefix.

**Single Lambda function for both routes.** Both the GET and PUT handlers talk to the same SSM parameter using the same boto3 client. Splitting them into two functions would mean more Terraform (two functions, two roles, two permissions) for no real benefit. If this grew to many routes with different concerns, I'd split them up.

## How I'd embellish the solution with more time

**Authentication on the PUT endpoint.** Right now anyone who finds the URL can update the string. I'd add API key authentication through API Gateway, or IAM auth for tighter control. The GET route would stay public so anyone can view the page.

**Input sanitization.** The dynamic string goes straight into HTML unescaped. Setting it to `<script>alert('xss')</script>` would execute JavaScript in the browser. Python's `html.escape()` would fix this in one line.

**CloudFront CDN.** Putting CloudFront in front of API Gateway would add caching (so Lambda doesn't run on every single page view) and serve content from edge locations closer to users.

**Monitoring and alerting.** CloudWatch alarms on Lambda errors, latency, and throttling. A dashboard showing request counts and response times. Right now if something breaks, nobody gets notified.

**CI/CD pipeline.** A GitHub Actions workflow that runs `terraform plan` on pull requests and `terraform apply` on merge to main. This catches issues before they hit production and creates an audit trail of infrastructure changes.

**Remote state backend.** Moving Terraform state from a local file to S3 with DynamoDB locking. This is essential for team collaboration since without it, two people running `terraform apply` at the same time could corrupt the state.

**Terraform tests.** Using the built-in `terraform test` framework to validate the configuration produces the expected resources and outputs before deploying.
