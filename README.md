# CRM

This project is a lightweight CRM system that manages accounts, contacts, products, purchase documents, sales documents, and tasks.

## Architecture

The codebase follows a repository and service pattern to separate concerns:

- **Repositories** encapsulate data-access logic and interact with the database. Each repository implements an interface that declares the supported operations.
- **Services** contain business rules and coordinate repository calls. Controllers/UI components depend on services rather than accessing the database directly.

For example, `CompanyService` coordinates address validation and persistence through `CompanyRepository` and `AddressService`.

## Running Tests

Install dependencies and run the test suite from the repository root:

```bash
pip install -r requirements.txt
pytest
```
