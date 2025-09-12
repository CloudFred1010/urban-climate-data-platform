# Urban Climate & Infrastructure Data Platform

## Project Overview
This project demonstrates the design and implementation of a production-grade data engineering pipeline that integrates multimodal datasets — geospatial, climate, and demographic data — into a unified cloud-native analytics platform.

The aim is to simulate a real-world scenario faced by governments, NGOs, and enterprises in the Global South: the need to combine fragmented datasets to generate actionable insights on climate resilience, infrastructure planning, and population risk management.

By building this project, we showcase expertise across the full data engineering lifecycle, including data ingestion, ETL, orchestration, cloud data services, CI/CD automation, monitoring, and data visualisation. The project also demonstrates how prepared data can be extended for machine learning applications using AWS SageMaker.

---

## Why This Project
Urban centres across the world face increasing challenges from climate change, including flooding, heatwaves, and other environmental risks. Decision-makers require integrated data platforms that combine:

- Geospatial data: flood zones, road networks, land use  
- Climate data: rainfall, temperature, extreme events  
- Demographic data: population density, household vulnerability  

Today, these datasets are often siloed across different systems, making it difficult to generate timely insights for risk mitigation and urban planning.

This project addresses that problem by demonstrating how to build a scalable, secure, and automated data pipeline that ingests, transforms, validates, and fuses these datasets into a cloud-based warehouse. The end result enables visualisation in QGIS and prepares the data for downstream analytics and machine learning models.

---

## Project Goals
1. Ingestion and Fusion: Automate the collection of geospatial, climate, and demographic datasets from public APIs and open data portals.  
2. ETL and Data Engineering: Clean, validate, and transform raw datasets into structured schemas optimised for analytics.  
3. Workflow Orchestration: Build robust Apache Airflow DAGs to schedule, monitor, and retry pipeline tasks.  
4. Cloud-Native Architecture: Leverage AWS services (S3, Redshift, EMR, Lambda, CloudWatch, SageMaker) to build a resilient, scalable data platform.  
5. CI/CD Integration: Use GitHub Actions to enforce quality checks, automate deployments, and integrate security scanning into the pipeline.  
6. Data Quality and Monitoring: Implement validation tests and monitoring to ensure trustworthy, reliable datasets.  
7. Visualisation: Enable policymakers and analysts to view results in QGIS, including maps that highlight areas of urban vulnerability.  
8. AI/ML Extension: Train a simple predictive model in SageMaker to demonstrate how data engineering work supports AI readiness.  

---

## Data Sources
**Geospatial Data**  
- OpenStreetMap (GeoJSON or Shapefiles for roads, land use, flood zones)  
- Ordnance Survey Open Data (UK-specific datasets)  
- UN OCHA Humanitarian Data Exchange (HDX) for global risk maps  

**Climate Data**  
- OpenWeatherMap API (historical and forecast rainfall, temperature)  
- NOAA Climate Data Online (long-term climate observations)  
- World Bank Climate Knowledge Portal  

**Demographic Data**  
- UK Office for National Statistics (ONS) Census datasets  
- WorldPop (global gridded population datasets)  
- UN Data or World Bank Open Data (population and socio-economic indicators)  

These datasets are freely accessible, ensuring that anyone replicating this project can build the pipeline end-to-end without proprietary barriers.

---

## Expected Outcomes
- A fully automated data pipeline that ingests, cleans, and integrates multimodal data  
- A cloud-based data warehouse (AWS Redshift) storing harmonised datasets  
- Airflow DAGs managing end-to-end workflows with retries and alerting  
- CI/CD pipelines in GitHub Actions ensuring secure, tested, and repeatable deployments  
- Monitoring dashboards and automated remediation using AWS CloudWatch and Lambda  
- QGIS maps showing urban areas at greatest risk from climate factors combined with population exposure  
- An optional SageMaker ML model that predicts vulnerability scores, demonstrating AI-readiness  

---

## Why It Matters for a Senior Data Engineer Role
This project is designed to test and showcase the full spectrum of skills required in a Senior Data Engineer role:

- Data engineering: Designing and implementing ETL pipelines with Python, Pandas, and PySpark  
- Orchestration: Building production workflows in Airflow  
- Cloud engineering: Deploying and maintaining AWS data services (S3, EMR, Redshift, Lambda, Athena, SageMaker)  
- CI/CD automation: Implementing GitHub Actions pipelines for testing, deployment, and security checks  
- Data quality: Embedding validation and monitoring to ensure reliability  
- Visualisation and analytics: Preparing data for QGIS and BI tools  
- Scalability and security: Using Terraform for reproducible infrastructure, IAM for least-privilege access, and container scanning for compliance  

---

## Phase-by-Phase Build Plan

### Phase 1 – Project Setup
**Objective**: Establish repository, environments, and infrastructure  
**Tools**: GitHub, Python 3.11+, PySpark, Docker, Terraform, AWS CLI, QGIS  

**Tasks**:  
- Create GitHub repository `urban-climate-data-platform`  
- Define repository structure:  
  - `/etl` – Python & PySpark ETL scripts  
  - `/dags` – Airflow DAGs  
  - `/infra` – Terraform IaC (S3, Redshift, EMR, Lambda)  
  - `/tests` – Unit/data quality tests  
  - `/ml` – SageMaker model (optional)  
  - `/.github/workflows` – GitHub Actions CI/CD  
  - `/docs` – Architecture diagrams + README  
- Setup pre-commit hooks (Black, Flake8, Gitleaks)  
- Provision AWS S3 bucket and Redshift cluster with Terraform  

### Phase 2 – Data Ingestion
**Objective**: Ingest multimodal datasets  
**Tools**: Python (Requests, Pandas), S3, API connectors  

**Tasks**:  
- Write Python scripts to fetch geospatial, climate, and demographic data  
- Store raw datasets in S3/raw/  
- Secure API keys using AWS Secrets Manager  
- Configure GitHub Action to trigger daily ingestion  

### Phase 3 – ETL Processing
**Objective**: Clean, transform, and unify datasets  
**Tools**: Pandas, PySpark (on EMR), SQL (Postgres/Redshift)  

**Tasks**:  
- Use Pandas to clean demographic CSV/Excel datasets  
- Use PySpark to join climate and geospatial data  
- Compute an Urban Vulnerability Index = rainfall × flood zone × population density  
- Load transformed tables into Redshift schemas (staging, analytics)  
- Validate results with Great Expectations  

### Phase 4 – Orchestration
**Objective**: Automate workflows with dependencies  
**Tools**: Apache Airflow  

**Tasks**:  
- Create DAG with tasks: Extract → Transform → Load → Quality check → Notify  
- Configure retries, SLAs, and logging  
- Deploy DAGs to Airflow with GitHub Actions  

### Phase 5 – CI/CD and Security
**Objective**: Automate testing and deployment  
**Tools**: GitHub Actions, Terraform, Trivy, Gitleaks, SQLFluff  

**Tasks**:  
- CI: run PyTest, SQLFluff, Trivy, and Gitleaks on pull requests  
- CD: apply Terraform, push Docker ETL image to ECR, deploy DAGs  

### Phase 6 – Monitoring and Reliability
**Objective**: Ensure pipeline reliability  
**Tools**: AWS CloudWatch, Lambda  

**Tasks**:  
- Capture ingestion throughput and query performance metrics  
- Configure alarms for failed ETL jobs  
- Automate remediation with Lambda functions  
- Send alerts to Slack/SNS  

### Phase 7 – Visualisation
**Objective**: Present results  
**Tools**: QGIS, Power BI (optional)  

**Tasks**:  
- Export Redshift analytics.vulnerability_index to CSV/GeoJSON  
- Load data into QGIS  
- Create maps of high-risk zones combining flood, rainfall, and population  

### Phase 8 – SageMaker Extension (Optional)
**Objective**: Extend platform into AI/ML  
**Tools**: SageMaker, scikit-learn  

**Tasks**:  
- Export combined dataset from Redshift  
- Train regression/classification model to predict vulnerability  
- Deploy model endpoint with SageMaker  
- Extend CI/CD pipeline to retrain on new data  

### Phase 9 – Documentation and Delivery
**Objective**: Package project for portfolio  

**Deliverables**:  
- GitHub repository with code and workflows  
- Architecture diagram (AWS + Airflow + QGIS)  
- Documentation covering ETL flow, schema, monitoring, and troubleshooting  
- Screenshots of QGIS maps and Airflow runs  

---

## Tools Checklist
- **Core**: Python, Pandas, PySpark, SQL, Airflow, Terraform, GitHub Actions, AWS (S3, Redshift, EMR, Lambda, CloudWatch)  
- **Security**: AWS Secrets Manager, IAM least privilege, Trivy, Gitleaks  
- **Visualisation**: QGIS, Power BI (optional)  
- **Extension**: SageMaker (ML)  
