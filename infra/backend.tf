terraform {
  backend "s3" {
    bucket         = "urban-climate-tfstate"
    key            = "infra/terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
