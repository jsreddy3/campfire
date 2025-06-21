To run the database:
docker compose up -d db

To run the app:
uvicorn app.main:app --host 0.0.0.0 --port 8000

MUST DO IN XCODE:
1) Update the base URL to your computer's URL
2) click on the dream target (the blue thing at the root of the dir)
3) Go to Info
4) Find the list of Custom iOS Target Properties
5) Go to App Transport Security Settings -> Expand to Exception Domains -> add your IP address
6) Under your new IP address, copy the same keys with the same TRUE values that you see under the existing IP address
