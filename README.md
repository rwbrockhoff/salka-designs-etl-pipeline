# Sälka Designs: Automated ETL & Analytics Pipeline

Serverless ETL pipeline that automatically ingests Squarespace order data, validates quality, and
delivers weekly production reports via email.

**🔧 Technologies Used:** AWS Lambda, AWS Glue, Amazon RDS (PostgreSQL), Amazon S3, Amazon
EventBridge, Amazon SES, AWS Secrets Manager, VPC, Python, SQL, Pandas, Squarespace API

[View Website Blog Post Here](https://ryanbrockhoff.com/blog/data-analytics/salka-designs-automated-etl/)

## 🏗️ Architecture

![Architecture Diagram](/docs/salka-architecture-diagram.png)

## 📊 Features

- Automated weekly data ingestion from Squarespace API
- Data quality validation with AWS Glue
- Secure PostgreSQL storage with VPC isolation
- Automated Excel report generation and email delivery

## 📖 Documentation

- [Full Project Blog Post](docs/blog-post.md)
- [Architecture Diagrams](/docs/)
- [Database Queries (SQL)](/database/)
- [Lambda Functions](/lambda-functions/salka-orders-etl/)
- [Glue ETL Job](/glue-jobs/salka-orders-etl/)
- [Example Data](/examples/salka-orders-etl/)
