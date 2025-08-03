# CRM

This project is a lightweight CRM system that manages accounts, contacts, products, purchase documents, sales documents, and tasks.

## Architecture

The codebase follows a repository and service pattern to separate concerns:

- **Repositories** encapsulate data-access logic and interact with the database. Each repository implements an interface that declares the supported operations.
- **Services** contain business rules and coordinate repository calls. Controllers/UI components depend on services rather than accessing the database directly.

For example, `CompanyService` coordinates address validation and persistence through `CompanyRepository` and `AddressService`.

## Seeding the Database

Populate the application with sample data for local development:

```bash
Python .\scripts\sandbox_data.py
```

## Running Tests

Install dependencies and execute the test suite:

```bash
pip install -r requirements.txt
python .\scripts\test.py
```
