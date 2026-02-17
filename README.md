# Dynamic HTML Service

Serves an HTML page with a dynamic string that can be changed without redeploying.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [AWS CLI](https://aws.amazon.com/cli/) configured with valid credentials
- Python 3.x with boto3 (`pip install boto3`) for the update script

## Deploy

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Terraform will output the API URL when it's done.

## Usage

Open the URL in a browser to see the page:

```
<h1>The saved string is Hello, World!</h1>
```

Update the string (pick any method):

```bash
# via the API
curl -X PUT https://YOUR_API_URL/string \
  -H "Content-Type: application/json" \
  -d '{"value": "something new"}'

# via the helper script
python scripts/update_string.py "something new"

# via AWS CLI or powershell 
aws ssm put-parameter --name "/dynamic-html/dynamic-string" --value "Testing from AWS CLI" --overwrite

#via git bash
MSYS_NO_PATHCONV=1 aws ssm put-parameter --name '/dynamic-html/dynamic-string' --type String --value 'Testing from Git bash' --overwrite --region us-east-1
```

Refresh the page -- the string updates immediately.

## Tear down

```bash
cd terraform
terraform destroy
```

## Project structure

```
terraform/
  terraform.tf    - version constraints
  providers.tf    - AWS provider
  variables.tf    - input variables
  main.tf         - all resources (SSM, IAM, Lambda, API Gateway)
  outputs.tf      - API URL and parameter name
  lambda/
    handler.py    - Python Lambda function
scripts/
  update_string.py - CLI helper to update the string
SOLUTION.md        - architecture decisions and trade-offs
```
