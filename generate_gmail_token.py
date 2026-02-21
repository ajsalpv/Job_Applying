import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Could not refresh token: {e}")
                print("🔄 Forcing re-authentication...")
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                'gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    print("\n✅ SUCCESS! 'token.json' has been generated.")
    
    # Read and print the token for Render Env Var
    with open('token.json', 'r') as token:
        token_content = token.read()
        
    print("\n📋 FOR RENDER DEPLOYMENT (COPY THIS):")
    print("==================================================")
    print(token_content)
    print("==================================================")
    print("1. Go to Render Dashboard -> Environment Variables")
    print("2. Add Key: GMAIL_TOKEN_JSON")
    print("3. Paste the content above as the Value")
    
    print("\nAlso commit 'token.json' to GitHub if you want local file fallback.")

if __name__ == '__main__':
    main()
