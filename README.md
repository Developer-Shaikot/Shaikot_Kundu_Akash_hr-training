# HR Training Request Assignment

This repository contains the completed **HR Training Request Module** assignment for Odoo.

## Project Structure

- `hr_training_request/`: The actual Odoo module source code. **[Please read the detailed technical README inside this folder for security notes and assumptions](hr_training_request/README.md).**
- `docs/`: Assignment requirements, System Architecture Document (SAD), and Software Requirements Specification (SRS).
- `scripts/`: Utility scripts used during development and testing (e.g., Postman collections, powershell scripts).
- `docker-compose.yml`: Docker configuration to quickly spin up an Odoo 17 instance with this module mounted.

## How to Run Locally

If you'd like to test this module locally using Docker:

1. Start the Docker containers:
   ```bash
   docker compose up -d
   ```
2. Open your browser and navigate to: [http://localhost:8069](http://localhost:8069)
3. Log in with the default credentials:
   - **Database**: `hr_training`
   - **Email**: `saikatkundu43@gmail.com`
   - **Password**: `123456`

To view the database directly, pgAdmin is exposed on [http://localhost:5050](http://localhost:5050).
