# Heron Data - Join the Siege

## Julian Douglas

### Part 1: Enhancements

#### Limitations and Solutions

- **Problem:** The file naming system is quite restrictive and only accepts three extensions: `pdf`, `png`, `jpg`. Other formats like `.txt`, `.jpeg`, `.doc`, `.csv`, `.heic`, `.tiff`, etc., are not supported.  
  **Solution:** Add more extensions, with individual behavior for each.

- **Problem:** The function `classify_file()` is also very limiting. It is simply a string match.  
  For example, it checks if `drivers_license` is in the file name, then it's classified as a `drivers_licence`. With this alone, there are several issues, which would apply to most classes:
  - Spelling inconsistency ('license' vs 'licence').
  - Variations in how people refer to files, such as `driving_licence`, `license`, and different spellings.
  - Ambiguous file names like `invoice_bank_statement`, which could be either an invoice or a bank statement.

 **Solution:** The classifier should inspect not only the filenames but also the file contents. Use libraries like PyMuPDF/PyPDF2 for PDFs, Tesseract for images, python-docx for `.doc` files, and pandas/openpyxl for Excel files. Then, feed the data into an ML model for classification.

- **Problem:** The classifier will be slow if large documents or many documents are submitted at the same time because it processes synchronously, waiting for one document to complete before moving to the next.  
  **Solution:** Use asynchronous processing (such as Celery or Quart) and a task queue (such as Redis).

- **Problem:** There is no error handling except for wrong file types. If a file is corrupt or there is an error, a generic error is presented to the user, which may be frustrating.  
  **Solution:** Add more error handling and return a meaningful result to the user.

- **Problem:** There is no security. Anyone with access to the API request system (Python, Postman, terminal) could upload malicious files.  
  **Solution:** Implement authentication, such as using an API key or scanning for malware. Set file size limits to prevent DDoS attacks.

---

### Part 2: Productionising

#### How to Ensure It's Robust and Reliable?

1. **Error Handling and Alerts**  
   - Set up a system to track errors by integrating an analytics dashboard like Grafana through Prometheus. Log events such as successful file processing, errors, retries, response times, and error rates to identify bottlenecks.
   - Ensure the system fails gracefully with `try/except` blocks and provides meaningful messages to the user. Consider implementing a timeout feature and sending alerts when files take too long to process.
   - Set up health checks and task queue monitoring to track failed tasks.

2. **Load Balancing**  
   - If a lot of files are expected, use a load balancer like AWS Elastic. If deployed on a cloud platform like Azure, auto-scaling can be implemented to scale with demand.

3. **Data Validation and Security**  
   - Validate file format and size. This has been done by checking file extensions and implementing a maximum size variable in the code.
   - For better performance, consider training a model on actual data and regularly retraining it to keep it updated.
   - Ensure files are scanned for malware and implement an authentication system. Due to time constraints, this was not implemented in code.
   - Consider implementing a deletion system to remove files after a certain amount of time.


#### How to Deploy to Make It Accessible to Other Services and Users?

To deploy this service for access across all environments:
1. **Containerisation:** The program must be containerised using Docker. This will make it easy to deploy using a pipeline on services like Azure DevOps, supporting continuous integration and deployment.
2. **Cloud Deployment:** Use a cloud platform like AWS, GCP, or Heroku. For file storage, AWS S3 can be used.
3. **Frontend (Optional):** Create a front end that interacts with the API. Users can upload a file via an HTML form, and a POST request will be made to the API upon submission.


--- 

To run the code, simply clone the repo, and cd into it. Then run `python -m src.app` as per the original. Run `pytest` for tests as well. I wrote tests for each of the features I implemented.
