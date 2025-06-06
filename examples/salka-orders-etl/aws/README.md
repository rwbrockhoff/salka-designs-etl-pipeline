# AWS: Additional Technical Documentation

![Glue ETL](/examples/salka-orders-etl/aws/salka-visual-etl.png)

### Visual ETL Workflow

AWS Glue Visual ETL pipeline showing the complete data transformation process from S3 source through
data quality checks to final output.

![Data Quality Checks](/examples/salka-orders-etl/aws/salka-glue-dq-checks.png)

### Data Quality Checks

Automated data quality validation with 100% pass rate across 8 rules, ensuring data integrity
throughout the ETL process.

![Lambda Layers](/examples/salka-orders-etl/aws/salka-custom-lambda-layers.png)

### Additional Lambda Layers

Additional Python libraries packaged as Lambda layers required by the `generateSalkaReports.py`
function, including custom layers alongside AWS's managed Pandas layer.

![VPC Endpoints](/examples/salka-orders-etl/aws/salka-vpc-endpoints.png)

### VPC Endpoints

Interface/gateway endpoints for secure access to AWS services used within our VPC.

![VPC Subnets](/examples/salka-orders-etl/aws/salka-vpc-subnets.png)

### VPC Subnets: How I allowed developer access to the VPC

VPC architecture with private subnets for RDS and Glue services, with a public subnet for secure
developer access via EC2.

![Postico Local Access](/examples/salka-orders-etl/aws/salka-postico-ssh-access.png)

### Local SSH Access with Postico

Secure local access via SSH tunneling in Postico to RDS PostgreSQL instance for data exploration and
development work.

---

For a more detailed review, you can
[read the full blog post here.](https://ryanbrockhoff.com/blog/data-analytics/salka-designs-automated-etl/)
