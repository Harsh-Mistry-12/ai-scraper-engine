What kind of input is given?
- XLSX/CSV/JSON/XML File
- What are the key features we need to consider
- What is the approximate size of the input file?
- What is the frequency of the input file?
- Is there any custom format that we need to consider?

What is the output we want from the website?
- What fields we want to extract
- In what format we want the output
- How do we want to store the output
- Do we need to process the data in any way
- Is there any kind of custom output format that we require?

How do I scrap the websites?
1. Visit the website
2. Analyze if the data we're getting is static or dynamic
3. Analyze if there's an API available for the website
    - What kind of API's they are using RESTFUL/GRAPHQL
    - What authentication mechanism they are using
    - What rate limiting they are imposing
    - What kind of response format they are using JSON/XML/HTML
    - What kind of request format they are using GET/POST/PUT/DELETE
    - Is there any session created with API Key or any other mechanism?
    - What is the API Structure

    Once this is done, we need to search the APIs in the browser:
        - Which APIs are required to get the data we want
            - Which APIs are required to login into the website
            - Which APIs are required to get the data from the website
            - Which payload needs to be sent?
            - Is payload dependent on the user ID, cookies, sessions, IP, browser fingerprint?
            - What headers are required to send
            - What response format they are using
            - What is the API Structure

            - Are there any cookies or local storage required to send
            - Are there any sessions required to send
            - Are there any anti-scraping measures required to bypass

4. Analyze if the website is using any anti-scraping measures
    - CAPTCHA
    - Rate limiting
    - IP blocking
    - User-Agent checking
    - Session checking
    - Honeypot
    - IP Geolocation blocking
    - Browser fingerprinting
    - Mouse movements
    - Key press events
    - WebGL fingerprinting
    - Canvas fingerprinting
    - Audio fingerprinting
    - Plugin fingerprinting
    - Font fingerprinting
    - Screen resolution checking
    - Building the XPATH
    - Accessing the Elements
    - Sending requests
    - Sending the correct Headers

    Once this is done, we need to decide which technique to use:
        - Which technique to use
            - Direct browser access
            - Browser automation
            - API integration

5. Decide the tech stack to use
    - Do we need to store the DB persistently (MySQL/PostgreSQL)?
    - Do we need to store the data in cache (Redis)?
    - Do we need to store data in one time formats (JSON/XML/CSV/XLSX)?
