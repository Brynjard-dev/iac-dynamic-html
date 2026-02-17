#!/usr/bin/env python3
import argparse
import boto3


def main():
    parser = argparse.ArgumentParser(description="Update the dynamic string")
    parser.add_argument("value", help="The new string value")
    parser.add_argument("--parameter-name", default="/dynamic-html/dynamic-string")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    ssm = boto3.client("ssm", region_name=args.region)
    ssm.put_parameter(Name=args.parameter_name, Value=args.value, Overwrite=True)
    print(f"Updated to: {args.value}")


if __name__ == "__main__":
    main()
