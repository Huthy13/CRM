# Account Documents UI Manual Test

1. Launch the application with `python main.py`.
2. Navigate to the Accounts tab and open an existing vendor or create a new one.
3. In the account details popup, locate the **Documents** section.
4. Click **Upload** and choose a file from your system. Confirm it appears in the list with the correct type and filename.
5. Select the document and click **Open** to verify it opens with the default viewer.
6. Select the document and click **Delete**. Ensure it disappears from the list and the file is removed from the storage directory (default `uploaded_documents`).
