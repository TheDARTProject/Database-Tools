<div align="center">

# [DART Project Database Tools](https://thedartproject.github.io/)

![DART Tools Banner](https://github.com/TheDARTProject/.github/blob/main/SCREENSHOTS/The-DART-Project.png)

A collection of specialized Python tools for processing, validating, and analyzing threat intelligence.

</div>

## Tool Suite

### Data Validation Tools
1. **ASCII Username Validator**  
   `Tool-01-ASCII-Username-Validator.py`  
   Validates Discord usernames for ASCII compliance and flags non-ASCII characters that may indicate suspicious accounts.

2. **JSON Validation Checker**  
   `Tool-07-JSON-Validation-Checker.py`  
   Ensures JSON database files have valid syntax and structure before processing.

3. **URL Format Validator**  
   `Tool-19-URL-Format-Validator.py`  
   Standardizes and validates URL formats in threat data, correcting common issues.

### Data Processing Tools
4. **Chronological Case Sorter**  
   `Tool-02-Chronological-Case-Sorter.py`  
   Organizes threat cases by discovery timestamp for timeline analysis.

5. **Case Number Normalizer**  
   `Tool-03-Case-Number-Normalizer.py`  
   Standardizes case reference numbers across the entire dataset.

6. **Timestamp Verifier**  
   `Tool-18-Timestamp-Verifier.py`  
   Validates and adds missing timestamps to records using multiple fallback methods.

### Data Enrichment Tools
7. **Account Creation Date Extractor**  
   `Tool-08-Account-Creation-Date-Extractor.py`  
   Calculates Discord account creation dates from snowflake IDs.

8. **Geolocation Tagger**  
   `Tool-13-Geolocation-Tagger.py`  
   Adds geographic metadata using IPInfo API based on URL domains.

9. **URL Redirect Tracer**  
   `Tool-14-URL-Redirect-Tracer.py`  
   Follows and documents redirect chains in malicious URLs.

10. **URLScan Analyzer**  
    `Tool-17-URLScan-Analyzer.py`  
    Integrates with URLScan.io for detailed malicious URL analysis.

### Verification Tools
11. **Invite Validator**  
    `Tool-09-Invite-Validator.py`  
    Tests Discord invite links with rate limit handling.

12. **Account Status Verifier**  
    `Tool-12-Account-Status-Verifier.py`  
    Checks current status of compromised Discord accounts.

13. **Telegram Link Verifier**  
    `Tool-16-Telegram-Link-Verifier.py`  
    Validates Telegram links found in threat data.

### Analysis Tools
14. **Database Field Inspector**  
    `Tool-05-Database-Field-Inspector.py`  
    Analyzes unique values and field distributions across the database.

15. **Malicious Server Analyzer**  
    `Tool-11-Malicious-Server-Analyzer.py`  
    Gathers detailed information about malicious Discord servers.

16. **Server Threat Counter**  
    `Tool-15-Server-Threat-Counter.py`  
    Generates statistics on threat distribution across servers.

### Import/Export Tools
17. **Excel-to-JSON Importer**  
    `Tool-04-Excel-to-JSON-Importer.py`  
    Converts spreadsheet data to the DART JSON format.

18. **JSON-to-Excel Exporter**  
    `Tool-06-JSON-to-Excel-Exporter.py`  
    Exports threat data to Excel for external analysis.

### Utility Tools
19. **API Rate Limit Checker**  
    `Tool-10-API-Rate-Limit-Checker.py`  
    Tests Discord API limits to optimize tool performance.

20. **Temporary Data Cleaner**  
    `Tool-20-Temporary-Data-Cleaner.py`  
    Specialized utility for cleaning specific temporary fields.

<div align="center">

## [Support my work on Ko-Fi](https://ko-fi.com/thatsinewave)

## [Join my Discord server](https://discord.gg/2nHHHBWNDw)

</div>
